/*!
 * https://github.com/Starcounter-Jack/JSON-Patch
 * (c) 2017 Joachim Wester
 * MIT license
 */
var __extends = undefined && undefined.__extends || function() {
  var extendStatics = function(d, b) {
    extendStatics = Object.setPrototypeOf || {__proto__: []} instanceof Array && function(d2, b2) {
      d2.__proto__ = b2;
    } || function(d2, b2) {
      for (var p in b2)
        if (b2.hasOwnProperty(p))
          d2[p] = b2[p];
    };
    return extendStatics(d, b);
  };
  return function(d, b) {
    extendStatics(d, b);
    function __() {
      this.constructor = d;
    }
    d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
  };
}();
var _hasOwnProperty = Object.prototype.hasOwnProperty;
function hasOwnProperty(obj, key) {
  return _hasOwnProperty.call(obj, key);
}
function _objectKeys(obj) {
  if (Array.isArray(obj)) {
    var keys = new Array(obj.length);
    for (var k = 0; k < keys.length; k++) {
      keys[k] = "" + k;
    }
    return keys;
  }
  if (Object.keys) {
    return Object.keys(obj);
  }
  var keys = [];
  for (var i in obj) {
    if (hasOwnProperty(obj, i)) {
      keys.push(i);
    }
  }
  return keys;
}
function _deepClone(obj) {
  switch (typeof obj) {
    case "object":
      return JSON.parse(JSON.stringify(obj));
    case "undefined":
      return null;
    default:
      return obj;
  }
}
function isInteger(str) {
  var i = 0;
  var len = str.length;
  var charCode;
  while (i < len) {
    charCode = str.charCodeAt(i);
    if (charCode >= 48 && charCode <= 57) {
      i++;
      continue;
    }
    return false;
  }
  return true;
}
function escapePathComponent(path) {
  if (path.indexOf("/") === -1 && path.indexOf("~") === -1)
    return path;
  return path.replace(/~/g, "~0").replace(/\//g, "~1");
}
function unescapePathComponent(path) {
  return path.replace(/~1/g, "/").replace(/~0/g, "~");
}
function hasUndefined(obj) {
  if (obj === void 0) {
    return true;
  }
  if (obj) {
    if (Array.isArray(obj)) {
      for (var i = 0, len = obj.length; i < len; i++) {
        if (hasUndefined(obj[i])) {
          return true;
        }
      }
    } else if (typeof obj === "object") {
      var objKeys = _objectKeys(obj);
      var objKeysLength = objKeys.length;
      for (var i = 0; i < objKeysLength; i++) {
        if (hasUndefined(obj[objKeys[i]])) {
          return true;
        }
      }
    }
  }
  return false;
}
function patchErrorMessageFormatter(message, args) {
  var messageParts = [message];
  for (var key in args) {
    var value = typeof args[key] === "object" ? JSON.stringify(args[key], null, 2) : args[key];
    if (typeof value !== "undefined") {
      messageParts.push(key + ": " + value);
    }
  }
  return messageParts.join("\n");
}
var PatchError = function(_super) {
  __extends(PatchError2, _super);
  function PatchError2(message, name, index, operation, tree) {
    var _newTarget = this.constructor;
    var _this = _super.call(this, patchErrorMessageFormatter(message, {name, index, operation, tree})) || this;
    _this.name = name;
    _this.index = index;
    _this.operation = operation;
    _this.tree = tree;
    Object.setPrototypeOf(_this, _newTarget.prototype);
    _this.message = patchErrorMessageFormatter(message, {name, index, operation, tree});
    return _this;
  }
  return PatchError2;
}(Error);

var JsonPatchError = PatchError;
var deepClone = _deepClone;
var objOps = {
  add: function(obj, key, document) {
    obj[key] = this.value;
    return {newDocument: document};
  },
  remove: function(obj, key, document) {
    var removed = obj[key];
    delete obj[key];
    return {newDocument: document, removed};
  },
  replace: function(obj, key, document) {
    var removed = obj[key];
    obj[key] = this.value;
    return {newDocument: document, removed};
  },
  move: function(obj, key, document) {
    var removed = getValueByPointer(document, this.path);
    if (removed) {
      removed = _deepClone(removed);
    }
    var originalValue = applyOperation(document, {op: "remove", path: this.from}).removed;
    applyOperation(document, {op: "add", path: this.path, value: originalValue});
    return {newDocument: document, removed};
  },
  copy: function(obj, key, document) {
    var valueToCopy = getValueByPointer(document, this.from);
    applyOperation(document, {op: "add", path: this.path, value: _deepClone(valueToCopy)});
    return {newDocument: document};
  },
  test: function(obj, key, document) {
    return {newDocument: document, test: _areEquals(obj[key], this.value)};
  },
  _get: function(obj, key, document) {
    this.value = obj[key];
    return {newDocument: document};
  }
};
var arrOps = {
  add: function(arr, i, document) {
    if (isInteger(i)) {
      arr.splice(i, 0, this.value);
    } else {
      arr[i] = this.value;
    }
    return {newDocument: document, index: i};
  },
  remove: function(arr, i, document) {
    var removedList = arr.splice(i, 1);
    return {newDocument: document, removed: removedList[0]};
  },
  replace: function(arr, i, document) {
    var removed = arr[i];
    arr[i] = this.value;
    return {newDocument: document, removed};
  },
  move: objOps.move,
  copy: objOps.copy,
  test: objOps.test,
  _get: objOps._get
};
function getValueByPointer(document, pointer) {
  if (pointer == "") {
    return document;
  }
  var getOriginalDestination = {op: "_get", path: pointer};
  applyOperation(document, getOriginalDestination);
  return getOriginalDestination.value;
}
function applyOperation(document, operation, validateOperation, mutateDocument, banPrototypeModifications, index) {
  if (validateOperation === void 0) {
    validateOperation = false;
  }
  if (mutateDocument === void 0) {
    mutateDocument = true;
  }
  if (banPrototypeModifications === void 0) {
    banPrototypeModifications = true;
  }
  if (index === void 0) {
    index = 0;
  }
  if (validateOperation) {
    if (typeof validateOperation == "function") {
      validateOperation(operation, 0, document, operation.path);
    } else {
      validator(operation, 0);
    }
  }
  if (operation.path === "") {
    var returnValue = {newDocument: document};
    if (operation.op === "add") {
      returnValue.newDocument = operation.value;
      return returnValue;
    } else if (operation.op === "replace") {
      returnValue.newDocument = operation.value;
      returnValue.removed = document;
      return returnValue;
    } else if (operation.op === "move" || operation.op === "copy") {
      returnValue.newDocument = getValueByPointer(document, operation.from);
      if (operation.op === "move") {
        returnValue.removed = document;
      }
      return returnValue;
    } else if (operation.op === "test") {
      returnValue.test = _areEquals(document, operation.value);
      if (returnValue.test === false) {
        throw new JsonPatchError("Test operation failed", "TEST_OPERATION_FAILED", index, operation, document);
      }
      returnValue.newDocument = document;
      return returnValue;
    } else if (operation.op === "remove") {
      returnValue.removed = document;
      returnValue.newDocument = null;
      return returnValue;
    } else if (operation.op === "_get") {
      operation.value = document;
      return returnValue;
    } else {
      if (validateOperation) {
        throw new JsonPatchError("Operation `op` property is not one of operations defined in RFC-6902", "OPERATION_OP_INVALID", index, operation, document);
      } else {
        return returnValue;
      }
    }
  } else {
    if (!mutateDocument) {
      document = _deepClone(document);
    }
    var path = operation.path || "";
    var keys = path.split("/");
    var obj = document;
    var t = 1;
    var len = keys.length;
    var existingPathFragment = void 0;
    var key = void 0;
    var validateFunction = void 0;
    if (typeof validateOperation == "function") {
      validateFunction = validateOperation;
    } else {
      validateFunction = validator;
    }
    while (true) {
      key = keys[t];
      if (banPrototypeModifications && key == "__proto__") {
        throw new TypeError("JSON-Patch: modifying `__proto__` prop is banned for security reasons, if this was on purpose, please set `banPrototypeModifications` flag false and pass it to this function. More info in fast-json-patch README");
      }
      if (validateOperation) {
        if (existingPathFragment === void 0) {
          if (obj[key] === void 0) {
            existingPathFragment = keys.slice(0, t).join("/");
          } else if (t == len - 1) {
            existingPathFragment = operation.path;
          }
          if (existingPathFragment !== void 0) {
            validateFunction(operation, 0, document, existingPathFragment);
          }
        }
      }
      t++;
      if (Array.isArray(obj)) {
        if (key === "-") {
          key = obj.length;
        } else {
          if (validateOperation && !isInteger(key)) {
            throw new JsonPatchError("Expected an unsigned base-10 integer value, making the new referenced value the array element with the zero-based index", "OPERATION_PATH_ILLEGAL_ARRAY_INDEX", index, operation, document);
          } else if (isInteger(key)) {
            key = ~~key;
          }
        }
        if (t >= len) {
          if (validateOperation && operation.op === "add" && key > obj.length) {
            throw new JsonPatchError("The specified index MUST NOT be greater than the number of elements in the array", "OPERATION_VALUE_OUT_OF_BOUNDS", index, operation, document);
          }
          var returnValue = arrOps[operation.op].call(operation, obj, key, document);
          if (returnValue.test === false) {
            throw new JsonPatchError("Test operation failed", "TEST_OPERATION_FAILED", index, operation, document);
          }
          return returnValue;
        }
      } else {
        if (key && key.indexOf("~") != -1) {
          key = unescapePathComponent(key);
        }
        if (t >= len) {
          var returnValue = objOps[operation.op].call(operation, obj, key, document);
          if (returnValue.test === false) {
            throw new JsonPatchError("Test operation failed", "TEST_OPERATION_FAILED", index, operation, document);
          }
          return returnValue;
        }
      }
      obj = obj[key];
    }
  }
}
function applyPatch(document, patch, validateOperation, mutateDocument, banPrototypeModifications) {
  if (mutateDocument === void 0) {
    mutateDocument = true;
  }
  if (banPrototypeModifications === void 0) {
    banPrototypeModifications = true;
  }
  if (validateOperation) {
    if (!Array.isArray(patch)) {
      throw new JsonPatchError("Patch sequence must be an array", "SEQUENCE_NOT_AN_ARRAY");
    }
  }
  if (!mutateDocument) {
    document = _deepClone(document);
  }
  var results = new Array(patch.length);
  for (var i = 0, length_1 = patch.length; i < length_1; i++) {
    results[i] = applyOperation(document, patch[i], validateOperation, true, banPrototypeModifications, i);
    document = results[i].newDocument;
  }
  results.newDocument = document;
  return results;
}
function applyReducer(document, operation, index) {
  var operationResult = applyOperation(document, operation);
  if (operationResult.test === false) {
    throw new JsonPatchError("Test operation failed", "TEST_OPERATION_FAILED", index, operation, document);
  }
  return operationResult.newDocument;
}
function validator(operation, index, document, existingPathFragment) {
  if (typeof operation !== "object" || operation === null || Array.isArray(operation)) {
    throw new JsonPatchError("Operation is not an object", "OPERATION_NOT_AN_OBJECT", index, operation, document);
  } else if (!objOps[operation.op]) {
    throw new JsonPatchError("Operation `op` property is not one of operations defined in RFC-6902", "OPERATION_OP_INVALID", index, operation, document);
  } else if (typeof operation.path !== "string") {
    throw new JsonPatchError("Operation `path` property is not a string", "OPERATION_PATH_INVALID", index, operation, document);
  } else if (operation.path.indexOf("/") !== 0 && operation.path.length > 0) {
    throw new JsonPatchError('Operation `path` property must start with "/"', "OPERATION_PATH_INVALID", index, operation, document);
  } else if ((operation.op === "move" || operation.op === "copy") && typeof operation.from !== "string") {
    throw new JsonPatchError("Operation `from` property is not present (applicable in `move` and `copy` operations)", "OPERATION_FROM_REQUIRED", index, operation, document);
  } else if ((operation.op === "add" || operation.op === "replace" || operation.op === "test") && operation.value === void 0) {
    throw new JsonPatchError("Operation `value` property is not present (applicable in `add`, `replace` and `test` operations)", "OPERATION_VALUE_REQUIRED", index, operation, document);
  } else if ((operation.op === "add" || operation.op === "replace" || operation.op === "test") && hasUndefined(operation.value)) {
    throw new JsonPatchError("Operation `value` property is not present (applicable in `add`, `replace` and `test` operations)", "OPERATION_VALUE_CANNOT_CONTAIN_UNDEFINED", index, operation, document);
  } else if (document) {
    if (operation.op == "add") {
      var pathLen = operation.path.split("/").length;
      var existingPathLen = existingPathFragment.split("/").length;
      if (pathLen !== existingPathLen + 1 && pathLen !== existingPathLen) {
        throw new JsonPatchError("Cannot perform an `add` operation at the desired path", "OPERATION_PATH_CANNOT_ADD", index, operation, document);
      }
    } else if (operation.op === "replace" || operation.op === "remove" || operation.op === "_get") {
      if (operation.path !== existingPathFragment) {
        throw new JsonPatchError("Cannot perform the operation at a path that does not exist", "OPERATION_PATH_UNRESOLVABLE", index, operation, document);
      }
    } else if (operation.op === "move" || operation.op === "copy") {
      var existingValue = {op: "_get", path: operation.from, value: void 0};
      var error = validate([existingValue], document);
      if (error && error.name === "OPERATION_PATH_UNRESOLVABLE") {
        throw new JsonPatchError("Cannot perform the operation from a path that does not exist", "OPERATION_FROM_UNRESOLVABLE", index, operation, document);
      }
    }
  }
}
function validate(sequence, document, externalValidator) {
  try {
    if (!Array.isArray(sequence)) {
      throw new JsonPatchError("Patch sequence must be an array", "SEQUENCE_NOT_AN_ARRAY");
    }
    if (document) {
      applyPatch(_deepClone(document), _deepClone(sequence), externalValidator || true);
    } else {
      externalValidator = externalValidator || validator;
      for (var i = 0; i < sequence.length; i++) {
        externalValidator(sequence[i], i, document, void 0);
      }
    }
  } catch (e) {
    if (e instanceof JsonPatchError) {
      return e;
    } else {
      throw e;
    }
  }
}
function _areEquals(a, b) {
  if (a === b)
    return true;
  if (a && b && typeof a == "object" && typeof b == "object") {
    var arrA = Array.isArray(a), arrB = Array.isArray(b), i, length, key;
    if (arrA && arrB) {
      length = a.length;
      if (length != b.length)
        return false;
      for (i = length; i-- !== 0; )
        if (!_areEquals(a[i], b[i]))
          return false;
      return true;
    }
    if (arrA != arrB)
      return false;
    var keys = Object.keys(a);
    length = keys.length;
    if (length !== Object.keys(b).length)
      return false;
    for (i = length; i-- !== 0; )
      if (!b.hasOwnProperty(keys[i]))
        return false;
    for (i = length; i-- !== 0; ) {
      key = keys[i];
      if (!_areEquals(a[key], b[key]))
        return false;
    }
    return true;
  }
  return a !== a && b !== b;
}

var core = /*#__PURE__*/Object.freeze({
  __proto__: null,
  JsonPatchError: JsonPatchError,
  deepClone: deepClone,
  getValueByPointer: getValueByPointer,
  applyOperation: applyOperation,
  applyPatch: applyPatch,
  applyReducer: applyReducer,
  validator: validator,
  validate: validate,
  _areEquals: _areEquals
});

/*!
 * https://github.com/Starcounter-Jack/JSON-Patch
 * (c) 2017 Joachim Wester
 * MIT license
 */
var beforeDict = new WeakMap();
var Mirror = function() {
  function Mirror2(obj) {
    this.observers = new Map();
    this.obj = obj;
  }
  return Mirror2;
}();
var ObserverInfo = function() {
  function ObserverInfo2(callback, observer) {
    this.callback = callback;
    this.observer = observer;
  }
  return ObserverInfo2;
}();
function getMirror(obj) {
  return beforeDict.get(obj);
}
function getObserverFromMirror(mirror, callback) {
  return mirror.observers.get(callback);
}
function removeObserverFromMirror(mirror, observer) {
  mirror.observers.delete(observer.callback);
}
function unobserve(root, observer) {
  observer.unobserve();
}
function observe(obj, callback) {
  var patches = [];
  var observer;
  var mirror = getMirror(obj);
  if (!mirror) {
    mirror = new Mirror(obj);
    beforeDict.set(obj, mirror);
  } else {
    var observerInfo = getObserverFromMirror(mirror, callback);
    observer = observerInfo && observerInfo.observer;
  }
  if (observer) {
    return observer;
  }
  observer = {};
  mirror.value = _deepClone(obj);
  if (callback) {
    observer.callback = callback;
    observer.next = null;
    var dirtyCheck = function() {
      generate(observer);
    };
    var fastCheck = function() {
      clearTimeout(observer.next);
      observer.next = setTimeout(dirtyCheck);
    };
    if (typeof window !== "undefined") {
      window.addEventListener("mouseup", fastCheck);
      window.addEventListener("keyup", fastCheck);
      window.addEventListener("mousedown", fastCheck);
      window.addEventListener("keydown", fastCheck);
      window.addEventListener("change", fastCheck);
    }
  }
  observer.patches = patches;
  observer.object = obj;
  observer.unobserve = function() {
    generate(observer);
    clearTimeout(observer.next);
    removeObserverFromMirror(mirror, observer);
    if (typeof window !== "undefined") {
      window.removeEventListener("mouseup", fastCheck);
      window.removeEventListener("keyup", fastCheck);
      window.removeEventListener("mousedown", fastCheck);
      window.removeEventListener("keydown", fastCheck);
      window.removeEventListener("change", fastCheck);
    }
  };
  mirror.observers.set(callback, new ObserverInfo(callback, observer));
  return observer;
}
function generate(observer, invertible) {
  if (invertible === void 0) {
    invertible = false;
  }
  var mirror = beforeDict.get(observer.object);
  _generate(mirror.value, observer.object, observer.patches, "", invertible);
  if (observer.patches.length) {
    applyPatch(mirror.value, observer.patches);
  }
  var temp = observer.patches;
  if (temp.length > 0) {
    observer.patches = [];
    if (observer.callback) {
      observer.callback(temp);
    }
  }
  return temp;
}
function _generate(mirror, obj, patches, path, invertible) {
  if (obj === mirror) {
    return;
  }
  if (typeof obj.toJSON === "function") {
    obj = obj.toJSON();
  }
  var newKeys = _objectKeys(obj);
  var oldKeys = _objectKeys(mirror);
  var deleted = false;
  for (var t = oldKeys.length - 1; t >= 0; t--) {
    var key = oldKeys[t];
    var oldVal = mirror[key];
    if (hasOwnProperty(obj, key) && !(obj[key] === void 0 && oldVal !== void 0 && Array.isArray(obj) === false)) {
      var newVal = obj[key];
      if (typeof oldVal == "object" && oldVal != null && typeof newVal == "object" && newVal != null) {
        _generate(oldVal, newVal, patches, path + "/" + escapePathComponent(key), invertible);
      } else {
        if (oldVal !== newVal) {
          if (invertible) {
            patches.push({op: "test", path: path + "/" + escapePathComponent(key), value: _deepClone(oldVal)});
          }
          patches.push({op: "replace", path: path + "/" + escapePathComponent(key), value: _deepClone(newVal)});
        }
      }
    } else if (Array.isArray(mirror) === Array.isArray(obj)) {
      if (invertible) {
        patches.push({op: "test", path: path + "/" + escapePathComponent(key), value: _deepClone(oldVal)});
      }
      patches.push({op: "remove", path: path + "/" + escapePathComponent(key)});
      deleted = true;
    } else {
      if (invertible) {
        patches.push({op: "test", path, value: mirror});
      }
      patches.push({op: "replace", path, value: obj});
    }
  }
  if (!deleted && newKeys.length == oldKeys.length) {
    return;
  }
  for (var t = 0; t < newKeys.length; t++) {
    var key = newKeys[t];
    if (!hasOwnProperty(mirror, key) && obj[key] !== void 0) {
      patches.push({op: "add", path: path + "/" + escapePathComponent(key), value: _deepClone(obj[key])});
    }
  }
}
function compare(tree1, tree2, invertible) {
  if (invertible === void 0) {
    invertible = false;
  }
  var patches = [];
  _generate(tree1, tree2, patches, "", invertible);
  return patches;
}

var duplex = /*#__PURE__*/Object.freeze({
  __proto__: null,
  unobserve: unobserve,
  observe: observe,
  generate: generate,
  compare: compare
});

Object.assign({}, core, duplex, {
  JsonPatchError: PatchError,
  deepClone: _deepClone,
  escapePathComponent: escapePathComponent,
  unescapePathComponent: unescapePathComponent
});

export { PatchError as P, _deepClone as _, applyOperation as a, applyPatch as b, applyReducer as c, validate as d, escapePathComponent as e, _areEquals as f, getValueByPointer as g, unobserve as h, generate as i, compare as j, observe as o, unescapePathComponent as u, validator as v };
