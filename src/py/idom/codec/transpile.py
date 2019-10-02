from html.parser import HTMLParser
from io import StringIO
from typing import Tuple, Optional, Sequence, List

# we need to import these because HTMLParser makes tags and attributes lowercase by
# default which we don't want - as a result we reimplement `HTMLParser.parse_starttag`
# without that behavior.
from html.parser import tagfind_tolerant, attrfind_tolerant, unescape  # type: ignore

from .utils import split_fstr_style_exprs, split_str_positional_format, transform_string


def transpile_html_templates(text: str) -> str:
    return transform_string(text, _transpile_html_templates, _TemplateTranspiler())


def _transpile_html_templates(
    text: str, index: int, transpiler: "_TemplateTranspiler"
) -> Tuple[int, Optional[str]]:
    if text[index : index + 4] != "html":
        return index + 1, None

    index += 4

    for str_char in ('"""', '"', "'''", "'"):
        # characters open a string
        if text[index : index + len(str_char)] == str_char:
            break
    else:
        return index + 1, None

    for forward_index in range(index + 1, len(text)):
        if text[forward_index : forward_index + len(str_char)] == str_char:
            template = text[index + len(str_char) : forward_index]
            py_code = transpiler.transpile(template.strip())
            return forward_index + len(str_char), py_code

    return forward_index + len(str_char), None


class _TemplateTranspiler(HTMLParser):
    def transpile(self, text: str) -> str:
        self._feed(text)
        code = self._read_code()
        self.reset()
        return code

    def feed(self, text: str) -> None:
        raise NotImplementedError()

    def _feed(self, text: str) -> None:
        return super().feed(self._load_exprs(text))

    def _read_code(self) -> str:
        self._code.seek(0)
        value = self._code.read()
        self._code.seek(self._cursor)
        return value[:-2]

    def reset(self) -> None:
        super().reset()
        self._exprs: List[str] = []
        self._cursor = 0
        self._code = StringIO()

    def handle_starttag(
        self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]
    ) -> None:
        self._write(f"html({self._substitute_exprs(tag)}, " + "{")
        subbed_attrs = [
            (
                self._substitute_exprs(k),
                self._substitute_exprs("true" if v is None else v),
            )
            for k, v in attrs
        ]
        self._write(", ".join("%s: %s" % item for item in subbed_attrs))
        self._write("}, [")

    def handle_data(self, data: str) -> None:
        parts = []
        for is_expr, string in split_str_positional_format(data):
            if is_expr:
                parts.append(self._substitute_exprs(string))
            else:
                # no formating took place
                parts.append(repr(string))
        self._write(", ".join(parts))

    def handle_endtag(self, tag: str) -> None:
        self._write("]), ")

    def handle_startendtag(self, tag: str, attrs: Sequence[Tuple[str, str]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def parse_starttag(self, i: int) -> int:
        self.__starttag_text = None
        endpos = self.check_for_whole_start_tag(i)  # type: ignore
        if endpos < 0:
            return endpos  # type: ignore
        rawdata = self.rawdata  # type: ignore
        self.__starttag_text = rawdata[i:endpos]

        # Now parse the data between i+1 and j into a tag and attrs
        attrs = []
        match = tagfind_tolerant.match(rawdata, i + 1)
        assert match, "unexpected call to parse_starttag()"
        k = match.end()
        self.lasttag = tag = match.group(1)
        while k < endpos:
            m = attrfind_tolerant.match(rawdata, k)
            if not m:
                break
            attrname, rest, attrvalue = m.group(1, 2, 3)
            if not rest:
                attrvalue = None
            elif (
                attrvalue[:1] == "'" == attrvalue[-1:]
                or attrvalue[:1] == '"' == attrvalue[-1:]
            ):
                attrvalue = attrvalue[1:-1]
            if attrvalue:
                attrvalue = unescape(attrvalue)
            attrs.append((attrname, attrvalue))
            k = m.end()

        end = rawdata[k:endpos].strip()
        if end not in (">", "/>"):
            lineno, offset = self.getpos()
            if "\n" in self.__starttag_text:
                lineno = lineno + self.__starttag_text.count("\n")
                offset = len(self.__starttag_text) - self.__starttag_text.rfind("\n")
            else:
                offset = offset + len(self.__starttag_text)
            self.handle_data(rawdata[i:endpos])
            return endpos  # type: ignore
        if end.endswith("/>"):
            # XHTML-style empty tag: <span attr="value" />
            self.handle_startendtag(tag, attrs)
        else:
            self.handle_starttag(tag, attrs)
            if tag in self.CDATA_CONTENT_ELEMENTS:  # type: ignore
                self.set_cdata_mode(tag)  # type: ignore
        return endpos  # type: ignore

    def _write(self, text: str) -> None:
        self._cursor += self._code.write(text)
        self._code.seek(self._cursor)

    def _load_exprs(self, text: str) -> str:
        parts: List[str] = []
        for is_expr, string in split_fstr_style_exprs(text):
            if is_expr:
                parts.append(f"{{{len(self._exprs)}}}")
                self._exprs.append(string)
            else:
                parts.append(string)
        return "".join(parts)

    def _substitute_exprs(self, text: str) -> str:
        result = text.format(*self._exprs)
        if result == text:
            # no formating took place
            return repr(text)
        else:
            # template syntax could be used inside the expression too
            return transpile_html_templates(result)
