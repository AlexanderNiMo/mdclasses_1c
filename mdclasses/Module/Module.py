from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Generator

from mdclasses.Module.ModuleParser import ModuleParser, ModuleBlock


class TextRange:

    def __init__(self, start: int, end: int):
        self.start_line = start
        self.end_line = end


class Parameter:

    def __init__(self,
                 name: str,
                 by_value: Optional[bool] = False,
                 default_value: Optional[str] = None):
        self.name = name.strip()
        self.by_value: bool = False if by_value is None else by_value
        self.default_value = None if default_value is None else default_value.strip()

    def __repr__(self):
        return f'{"Знач " if self.by_value else ""}' \
               f'{self.name}' \
               f'{"" if self.default_value is None else " = "}' \
               f'{"" if self.default_value is None else self.default_value}'


class ExpansionModifier:

    def __init__(self, modifier_type: str, sub_program_name: str):
        self.sub_program_name = sub_program_name
        self.modifier_type = modifier_type

    def __repr__(self):
        return f'&{self.modifier_type}(\"{self.sub_program_name}\")'


class CompilationDirective:

    def __init__(self, compilation_type: str):
        self.compilation_type = compilation_type

    def __repr__(self):
        return f'&{self.compilation_type}'


def mutable(f_setter):
    def warper(s, *args, **kwargs):
        s._ModuleElement__changed = True
        f_setter(s, *args, **kwargs)
    return warper


class ModuleElement(ABC):

    def __init__(self, start:int, end:int, text: str):
        self.text_range: TextRange = TextRange(start, end)
        self.__changed = False
        self.__original_text = text
        self.__text = text

    @property
    def text(self) -> str:
        if self.changed:
            self.__text = self._get_text()
            self.__changed = False
        return self.__text

    def _get_text(self) -> str:
        return self.__text

    @classmethod
    @abstractmethod
    def from_data(cls, data: ModuleBlock):
        pass

    def element_by_class(self, target_class: type) -> Generator:
        if self.__class__ == target_class:
            yield self

    @property
    def changed(self):
        return self.__changed


class Subordinates(ModuleElement):

    def __init__(self, start:int, end:int, text: str, end_text: str = '', elements: List['ModuleElement'] = None):
        super(Subordinates, self).__init__(start=start, end=end, text=text)
        self.__start_text: str = text
        self.__end_text: str = end_text
        self.__elements = list() if elements is None else elements

    def element_by_class(self, target_class: type) -> Generator:

        for el in super(Subordinates, self).element_by_class(target_class):
            yield el
        for element in self.elements:
            for sub_element in element.element_by_class(target_class):
                yield sub_element

    @property
    def end_text(self) -> str:
        return self.__end_text

    @property
    def changed(self):
        cur_changed = super(Subordinates, self).changed
        return any(element.changed for element in self.elements) or cur_changed

    @property
    def elements(self):
        return self.__elements

    @mutable
    def add_sub_element(self, element: ModuleElement):
        self.__elements.append(element)

    @property
    def text(self):
        text = list()
        text.append(super(Subordinates, self).text)
        text.append(self._get_elements_text())
        text.append(self._get_end_text())
        return '\n'.join(text)

    def _get_text(self):
        if super(Subordinates, self).changed:
            return self._get_title()
        else:
            return self.__start_text

    def _get_title(self):
        return ''

    def _get_end_text(self):
        return self.end_text

    def _get_elements_text(self):
        return '\n'.join(e.text for e in self.elements)


class TextData(ModuleElement):

    def __init__(self, text: str, start: int, end: int):
        super(TextData, self).__init__(start=start, end=end, text=text)
        self.__text_data: str = text

    @property
    def text_data(self) -> str:
        return self.__text_data

    @text_data.setter
    @mutable
    def text_data(self, value: str):
        self.__text_data = value

    def _get_text(self) -> str:
        return self.__text_data

    @classmethod
    def from_data(cls, data: ModuleBlock) -> 'TextData':
        return TextData(data.text, data.start, data.end)


class SubProgram(Subordinates):
    SUB_PROGRAM_TYPE = None
    SUB_PROGRAM_END = None

    def __init__(self,
                 name: str,
                 start: int,
                 end: int,
                 text: str,
                 end_text: str,
                 comments: Optional[str] = None,
                 compilation_directive: Optional[CompilationDirective] = None,
                 expansion_modifier: Optional[ExpansionModifier] = None,
                 params: Optional[List[Parameter]] = None,
                 public: Optional[bool] = None):

        super(SubProgram, self).__init__(start=start, end=end, text=text, end_text=end_text)

        self.__comments = comments
        self.__compilation_directive = compilation_directive
        self.__expansion_modifier = expansion_modifier
        self.__name = name

        self.__params: List[Parameter] = list() if params is None else params

        self.__public: bool = False if public is None else public

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    @mutable
    def name(self, value: str):
        self.__name = value

    @property
    def comments(self) -> str:
        return self.__comments

    @comments.setter
    @mutable
    def comments(self, value: str):
        self.__comments = value

    @property
    def compilation_directive(self) -> CompilationDirective:
        return self.__compilation_directive

    @compilation_directive.setter
    @mutable
    def compilation_directive(self, value: CompilationDirective):
        self.__compilation_directive = value

    @property
    def expansion_modifier(self) -> ExpansionModifier:
        return self.__expansion_modifier

    @expansion_modifier.setter
    @mutable
    def expansion_modifier(self, value: ExpansionModifier):
        self.__expansion_modifier = value

    @property
    def params(self) -> List[Parameter]:
        return self.__params

    @mutable
    def add_param(self, new_param: Parameter):
        self.__params.append(new_param)

    @mutable
    def del_param(self, param_name: str):
        self.__params.remove(filter(lambda x: x.name == param_name, self.__params)[0])

    @property
    def public(self) -> bool:
        return self.__public

    @public.setter
    @mutable
    def public(self, value: bool):
        self.__public = value

    def _get_title(self):
        comments = '' if self.comments is None else f'{self.comments}'

        directive = '' if self.compilation_directive is None else f'{str(self.compilation_directive)}\n'
        directive = directive if self.expansion_modifier is None else f'{directive}{str(self.expansion_modifier)}\n'

        params = ', '.join(str(v) for v in self.params)
        public = 'Экспорт' if self.public else ''
        title = f'{self.SUB_PROGRAM_TYPE} {self.name}({params}) {public}'

        return f'{comments}{directive}{title}'

    def _get_end_text(self):
        return self.end_text

    @classmethod
    def from_data(cls, data: ModuleBlock):
        objects = {
            'Функция': Function,
            'Процедура': Procedure,
        }
        additional_data = data.get_data()

        params = [Parameter(**param_data) for param_data in additional_data['params']]

        preproc = None
        if additional_data['preproc'] is not None:
            preproc = CompilationDirective(additional_data['preproc']['Directive'])

        expansion_modifier = None
        if additional_data['extension'] is not None:
            expansion_modifier = ExpansionModifier(
                additional_data['extension']['Directive'],
                additional_data['extension']['SubProgramName']
            )

        prog_data = dict(
            name=additional_data['name'],
            start=data.start,
            end=data.end,
            comments=None if additional_data['comment'] == '' else additional_data['comment'],
            compilation_directive=preproc,
            expansion_modifier=expansion_modifier,
            params=params,
            public=additional_data['public'],
            text=data.text,
            end_text=additional_data['ent_text']
        )

        return objects[additional_data['type']](**prog_data)

    def __repr__(self):
        return f'<{self.__class__.__name__}> {self.__name}'


class Function(SubProgram):
    SUB_PROGRAM_TYPE = 'Функция'
    SUB_PROGRAM_END = 'КонецФункции'


class Procedure(SubProgram):
    SUB_PROGRAM_TYPE = 'Процедура'
    SUB_PROGRAM_END = 'КонецПроцедуры'


class PreprocessorInstruction(Subordinates):

    def __init__(self, instruction_type: str, start: int, end: int, text: str, end_text: str, elements: Optional[List[ModuleElement]]=None):
        super(PreprocessorInstruction, self).__init__(
            start=start, end=end, elements=elements, text=text, end_text=end_text)
        self.__instruction_type = instruction_type

    @property
    def instruction_type(self):
        return self.__instruction_type

    @instruction_type.setter
    @mutable
    def instruction_type(self, value):
        self.__instruction_type = value

    def _get_title(self):
        return f'#Если {self.instruction_type} Тогда'

    @classmethod
    def from_data(cls, data: ModuleBlock):
        additional_data = data.get_data()
        return cls(additional_data['preprocessor_type'], start=data.start, end=data.end,
                   text=data.text, end_text=additional_data['ent_text'])


class Region(Subordinates):

    def __init__(self, name: str, text: str, start: int, end: int, end_text: str, elements: Optional[List[ModuleElement]] = None):
        super(Region, self).__init__(start=start, end=end, text=text, end_text=end_text, elements=elements)
        self.name: str = name

    @property
    def name(self):
        return self.__name

    @name.setter
    @mutable
    def name(self, value):
        self.__name = value

    def _get_title(self):
        return f'#Область {self.name}'

    @classmethod
    def from_data(cls, data: ModuleBlock):
        additional_data = data.get_data()
        return cls(name=additional_data['name'], start=data.start, end=data.end,
                   text=data.text, end_text=additional_data['ent_text'])

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name}>'


class Module(Subordinates):

    @classmethod
    def from_data(cls, data: ModuleBlock):
        return cls(data.text, data.start, data.end)

    def __init__(self, text: str, start: int, end: int, elements: Optional[List[ModuleElement]] = None):
        super(Module, self).__init__(start=start, end=end, elements=elements, text=text)

        self.__procedures = None
        self.__functions = None

    @property
    def text(self):
        return super(Subordinates, self).text

    def _get_text(self):
        return '\n'.join(e.text for e in self.elements)

    def functions(self) -> Generator:
        if self.__functions is None:
            self.__functions = list()
            for element in self.element_by_class(Function):
                self.__functions.append(element)
                yield element
        else:
            for element in self.__functions:
                yield element

    def procedures(self) -> Generator:
        if self.__procedures is None:
            self.__procedures = list()
            for element in self.element_by_class(Procedure):
                self.__procedures.append(element)
                yield element
        else:
            for element in self.__procedures:
                yield element


def create_module(parser: ModuleParser, module_text: str) -> Module:

    block = parser.parse_module_text(module_text)
    module = Module.from_data(block)

    for element in block.sub_elements:
        module.elements.append(_create_module_element(element))

    return module


def _create_module_element(element: ModuleBlock) -> ModuleElement:
    objects = {
        'text': TextData,
        'region': Region,
        'preprocessor': PreprocessorInstruction,
        'sub_program': SubProgram,
        'comment': TextData
    }

    module_element = objects[element.block_type].from_data(element)

    if isinstance(module_element, Subordinates):
        for sub_block in element.sub_elements:
            module_element.elements.append(_create_module_element(sub_block))

    return module_element