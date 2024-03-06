import asyncio
import base64
from dataclasses import asdict, is_dataclass
import datetime
import hashlib
import time
from collections.abc import Iterable
from decimal import Decimal
from logging import getLogger
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

import orjson
import pyotp
from more_itertools import chunked
from reactpy.backend.types import Location

logger = getLogger(__name__)


class StateRecoveryFailureError(Exception):
    """
    Raised when state recovery fails.
    """


class StateRecoveryManager:
    def __init__(
        self,
        serializable_types: Iterable[type],
        pepper: str,
        otp_key: str | None = None,
        otp_interval: int = (4 * 60 * 60),
        otp_digits: int = 10,  # 10 is the max allowed
        otp_max_age: int = (48 * 60 * 60),
        # OTP code is actually three codes, in the past and future concatenated
        otp_mixer: float = (365 * 24 * 60 * 60 * 3),
        max_num_state_objects: int = 512,
        max_object_length: int = 40000,
        default_serializer: Callable[[Any], bytes] | None = None,
        deserializer_map: dict[type, Callable[[Any], Any]] | None = None,
    ) -> None:
        self._pepper = pepper
        self._max_num_state_objects = max_num_state_objects
        self._max_object_length = max_object_length
        self._otp_key = base64.b32encode(
            (otp_key or self._discover_otp_key()).encode("utf-8")
        )
        self._totp = pyotp.TOTP(self._otp_key, digits=otp_digits, interval=otp_interval)
        self._otp_max_age = otp_max_age
        self._default_serializer = default_serializer
        self._deserializer_map = deserializer_map or {}
        self._otp_mixer = otp_mixer

        self._map_objects_to_ids(
            [
                *list(serializable_types),
                Decimal,
                datetime.datetime,
                datetime.date,
                datetime.time,
                datetime.timezone,
                datetime.timedelta,
                Location,
            ]
        )

    def _map_objects_to_ids(self, serializable_types: Iterable[type]) -> dict:
        self._object_to_type_id = {}
        self._type_id_to_object = {}
        for idx, typ in enumerate(
            (None, bool, str, int, float, list, tuple, UUID, datetime.timezone, datetime.timedelta, *serializable_types)
        ):
            idx_as_bytes = str(idx).encode("utf-8")
            self._object_to_type_id[typ] = idx_as_bytes
            self._type_id_to_object[idx_as_bytes] = typ

    def _discover_otp_key(self) -> str:
        """
        Generate an OTP key by looking at the parent directory of where
        ReactPy is installed and taking down the names and creation times
        of everything in there.
        """
        hasher = hashlib.sha256()
        parent_dir_of_root = Path(__file__).parent.parent.parent
        for thing in parent_dir_of_root.iterdir():
            hasher.update((thing.name + str(thing.stat().st_ctime)).encode("utf-8"))
        return hasher.hexdigest()

    def create_serializer(
        self, salt: str, target_time: float | None = None
    ) -> "StateRecoverySerializer":
        return StateRecoverySerializer(
            totp=self._totp,
            target_time=target_time,
            otp_max_age=self._otp_max_age,
            otp_mixer=self._otp_mixer,
            pepper=self._pepper,
            salt=salt,
            object_to_type_id=self._object_to_type_id,
            type_id_to_object=self._type_id_to_object,
            max_object_length=self._max_object_length,
            max_num_state_objects=self._max_num_state_objects,
            default_serializer=self._default_serializer,
            deserializer_map=self._deserializer_map,
        )


class StateRecoverySerializer:

    def __init__(
        self,
        totp: pyotp.TOTP,
        target_time: float | None,
        otp_max_age: int,
        otp_mixer: float,
        pepper: str,
        salt: str,
        object_to_type_id: dict[Any, bytes],
        type_id_to_object: dict[bytes, Any],
        max_object_length: int,
        max_num_state_objects: int,
        default_serializer: Callable[[Any], bytes] | None = None,
        deserializer_map: dict[type, Callable[[Any], Any]] | None = None,
    ) -> None:
        self._totp = totp
        self._otp_mixer = otp_mixer
        target_time = target_time or time.time()
        self._target_time = target_time
        otp_code = self._get_otp_code(target_time)
        self._otp_max_age = otp_max_age
        self._otp_code = otp_code.encode("utf-8")
        self._pepper = pepper.encode("utf-8")
        self._salt = salt.encode("utf-8")
        self._object_to_type_id = object_to_type_id
        self._type_id_to_object = type_id_to_object
        self._max_object_length = max_object_length
        self._max_num_state_objects = max_num_state_objects
        self._provided_default_serializer = default_serializer
        deserialization_map = {
            datetime.timezone: lambda x: datetime.timezone(
                datetime.timedelta(**x["offset"]), x["name"]
            ),
        }
        self._deserializer_map = deserialization_map | (deserializer_map or {})

    def _get_otp_code(self, target_time: float) -> str:
        at = self._totp.at
        return f"{at(target_time)}{at(target_time - self._otp_mixer)}{at(target_time + self._otp_mixer)}"

    async def serialize_state_vars(
        self, state_vars: dict[str, Any]
    ) -> dict[str, tuple[str, str, str]]:
        if len(state_vars) > self._max_num_state_objects:
            logger.warning(
                f"State is too large ({len(state_vars)}). State will not be sent"
            )
            return {}
        result = {}
        for chunk in chunked(state_vars.items(), 50):
            for key, value in chunk:
                result[key] = self._serialize(key, value)
            await asyncio.sleep(0)  # relinquish CPU
        return result

    def _serialize(self, key: str, obj: object) -> tuple[str, str, str]:
        type_id = b"1"  # bool
        if obj is None:
            return "0", "", ""
        match obj:
            case True:
                result = b"true"
            case False:
                result = b"false"
            case _:
                obj_type = type(obj)
                if obj_type in (list, tuple):
                    if len(obj) != 0:
                        obj_type = type(obj[0])
                for t in obj_type.__mro__:
                    type_id = self._object_to_type_id.get(t)
                    if type_id:
                        break
                else:
                    raise ValueError(
                        f"Objects of type {obj_type} was not part of serializable_types"
                    )
                result = self._serialize_object(obj)
                if len(result) > self._max_object_length:
                    raise ValueError(
                        f"Serialized object {obj} is too long (length: {len(result)})"
                    )
        signature = self._sign_serialization(key, type_id, result)
        return (
            type_id.decode("utf-8"),
            base64.urlsafe_b64encode(result).decode("utf-8"),
            signature,
        )

    def deserialize_client_state(
        self, state_vars: dict[str, tuple[str, str, str]]
    ) -> None:
        return {
            key: self._deserialize(key, type_id.encode("utf-8"), data, signature)
            for key, (type_id, data, signature) in state_vars.items()
        }

    def _deserialize(
        self, key: str, type_id: bytes, data: bytes, signature: str
    ) -> Any:
        if type_id == b"0":
            return None
        try:
            typ = self._type_id_to_object[type_id]
        except KeyError as err:
            raise StateRecoveryFailureError(f"Unknown type id {type_id}") from err

        result = base64.urlsafe_b64decode(data)
        expected_signature = self._sign_serialization(key, type_id, result)
        if expected_signature != signature:
            if not self._try_future_code(key, type_id, result, signature):
                if not self._try_older_codes_and_see_if_one_checks_out(
                    key, type_id, result, signature
                ):
                    raise StateRecoveryFailureError(
                        f"Signature mismatch for type id {type_id}"
                    )
        return self._deserialize_object(typ, result)

    def _try_future_code(
        self, key: str, type_id: bytes, data: bytes, signature: str
    ) -> bool:
        future_time = self._target_time + self._totp.interval
        otp_code = self._get_otp_code(future_time).encode("utf-8")
        return self._sign_serialization(key, type_id, data, otp_code) == signature

    def _try_older_codes_and_see_if_one_checks_out(
        self, key: str, type_id: bytes, data: bytes, signature: str
    ) -> bool:
        past_time = self._target_time
        for _ in range(100):
            past_time -= self._totp.interval
            otp_code = self._get_otp_code(past_time).encode("utf-8")
            if self._sign_serialization(key, type_id, data, otp_code) == signature:
                return True
            if past_time < self._target_time - self._otp_max_age:
                return False
        raise RuntimeError("Too many iterations: _try_older_codes_and_see_if_one_checks_out")

    def _sign_serialization(
        self, key: str, type_id: bytes, data: bytes, otp_code: bytes | None = None
    ) -> str:
        hasher = hashlib.sha256()
        hasher.update(type_id)
        hasher.update(data)
        hasher.update(self._pepper)
        hasher.update(otp_code or self._otp_code)
        hasher.update(self._salt)
        hasher.update(key.encode("utf-8"))
        return hasher.hexdigest()

    def _serialize_object(self, obj: Any) -> bytes:
        return orjson.dumps(obj, default=self._default_serializer)

    def _default_serializer(self, obj: Any) -> bytes:
        if isinstance(obj, datetime.timezone):
            return {"name": obj.tzname(None), "offset": obj.utcoffset(None)}
        if isinstance(obj, datetime.timedelta):
            return {"days": obj.days, "seconds": obj.seconds, "microseconds": obj.microseconds}
        if is_dataclass(obj):
            return asdict(obj)
        if self._provided_default_serializer:
            return self._provided_default_serializer(obj)
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    def _do_deserialize(
        self, typ: type, result: Any, custom_deserializer: Callable | None
    ) -> Any:
        if custom_deserializer:
            return custom_deserializer(result)
        if isinstance(result, str):
            return typ(result)
        if isinstance(result, dict):
            return typ(**result)
        return result

    def _deserialize_object(self, typ: Any, data: bytes) -> Any:
        if typ is None and not data:
            return None
        result = orjson.loads(data)
        custom_deserializer = self._deserializer_map.get(typ)
        if type(result) in (list, tuple):
            return [
                self._do_deserialize(typ, item, custom_deserializer) for item in result
            ]
        return self._do_deserialize(typ, result, custom_deserializer)
