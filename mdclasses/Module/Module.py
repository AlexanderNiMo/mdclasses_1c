from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Generator, Union
import pathlib
import logging

from mdclasses.Module.ModuleParser import ModuleParser, ModuleBlock


logger = logging.getLogger(__name__)


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

    def __init__(self, start: int, end: int, text: str):
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

    def __init__(self, start: int, end: int, text: str, end_text: str = '', elements: List['ModuleElement'] = None):
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

    @mutable
    def insert_sub_element(self, element: ModuleElement, index: int):
        self.__elements.insert(index, element)

    @mutable
    def clear_sub_elements(self):
        self.__elements = []

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
        try:
            _param = next(filter(lambda x: x.name == param_name, self.__params))
        except StopIteration:
            raise KeyError(f'Нет такого параметра.')

        self.__params.remove(_param)

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

    @property
    def call_text(self):
        params = ', '.join(v.name for v in self.params)

        return f'{self.name}({params});'

    def _get_end_text(self):
        return self.end_text

    @classmethod
    def from_data(cls, data: ModuleBlock):
        objects = {
            'Функция'.upper(): Function,
            'Процедура'.upper(): Procedure,
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

        return objects[additional_data['type'].upper()](**prog_data)

    def __repr__(self):
        return f'<{self.__class__.__name__}> {self.__name}'


class Function(SubProgram):
    SUB_PROGRAM_TYPE = 'Функция'
    SUB_PROGRAM_END = 'КонецФункции'


class Procedure(SubProgram):
    SUB_PROGRAM_TYPE = 'Процедура'
    SUB_PROGRAM_END = 'КонецПроцедуры'


class PreprocessorInstruction(Subordinates):

    def __init__(self, instruction_type: str, start: int, end: int, text: str, end_text: str,
                 elements: Optional[List[ModuleElement]] = None):
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

    def __init__(self, name: str, text: str, start: int, end: int, end_text: str,
                 elements: Optional[List[ModuleElement]] = None):
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
        aditional_data = data.get_data()
        return cls(aditional_data['name'], aditional_data['path'], data.text, data.start, data.end)

    def __init__(self, name: str, path: pathlib.Path, text: str, start: int, end: int, elements: Optional[List[ModuleElement]] = None):
        super(Module, self).__init__(start=start, end=end, elements=elements, text=text)

        self._name: str = name
        self._path: pathlib.Path = path

        self.__procedures: Optional[Dict[str, Procedure]] = None
        self.__functions: Optional[Dict[str, Function]] = None

    @property
    def text(self):
        return super(Subordinates, self).text

    @property
    def name(self):
        return self._name

    @property
    def file_name(self) -> pathlib.Path:
        return self._path

    @property
    def module_variables_text(self):
        variables_elements = []
        for element in self.elements:
            if self.__have_sub_procedure(element):
                break
            variables_elements.append(element)
        module_variables_text = '\n'.join(e.text for e in variables_elements)
        if 'Перем '.upper() in module_variables_text.upper():
            return module_variables_text
        else:
            return ''

    @property
    def module_main_text(self):
        if self.module_variables_text == '':
            return self.text
        i = 0
        for i, element in enumerate(self.elements):
            if self.__have_sub_procedure(element):
                break

        return '\n'.join(e.text for e in self.elements[i:])

    def __have_sub_procedure(self, element: ModuleElement):
        if isinstance(element, SubProgram):
            return True
        if isinstance(element, Subordinates):
            return not all([not self.__have_sub_procedure(e) for e in element.elements])
        return False

    def _get_text(self):
        return '\n'.join(e.text for e in self.elements)

    def find_sub_program(self, name: str) -> Union[Procedure, Function]:

        def _find_by_name(proc_name: str, data: Optional[dict], gen: Generator):
            def filter_name(sub_proc: Union[Procedure, Function]) -> bool:
                return sub_proc.name == proc_name

            try:
                if data is None:
                    element = next(filter(filter_name, gen))
                else:
                    element = data[name]
            except (StopIteration, KeyError) as e:
                element = None

            return element

        sub_proc = _find_by_name(name, self.__functions, self.functions())

        if sub_proc is not None:
            return sub_proc

        sub_proc = _find_by_name(name, self.__procedures, self.procedures())

        if sub_proc is None:
            raise KeyError(f'В модуле нет подпрограммы {name}.')

        return sub_proc

    def functions(self) -> Generator:
        if self.__functions is None:
            self.__functions = dict()
            for element in self.element_by_class(Function):
                self.__functions[element.name] = element
                yield element
        else:
            for element in self.__functions.values():
                yield element

    def procedures(self) -> Generator:
        if self.__procedures is None:
            self.__procedures = dict()
            for element in self.element_by_class(Procedure):
                self.__procedures[element.name] = element
                yield element
        else:
            for element in self.__procedures.values():
                yield element

    def save_to_file(self):
        self._path.write_text(self.text, 'utf-8-sig')


def create_module(parser: ModuleParser, module_path: pathlib.Path) -> Module:
    try:
        module_text = module_path.read_text('utf-8-sig')

        block = parser.parse_module_text(module_text)
        block.add_data('name', module_path.stem)
        block.add_data('path', module_path)

        module = Module.from_data(block)

        for element in block.sub_elements:
            module.elements.append(_create_module_element(element))
    except Exception as ex:
        logger.error(f'Ошибка создания модуля из файла по пут {module_path}')
        raise ex

    return module


def _create_module_element(element: ModuleBlock) -> ModuleElement:
    objects = {
        'text': TextData,
        'region': Region,
        'preprocessor': PreprocessorInstruction,
        'sub_program': SubProgram,
        'comment': TextData,
        'preproc': TextData
    }

    try:
        module_element = objects[element.block_type].from_data(element)
    except KeyError as ex:
        logger.error(f'Получения класса-конструктора по типу {element.block_type} '
                     f'Данные элемента: {element.block_type}')
        raise ex

    if isinstance(module_element, Subordinates):
        for sub_block in element.sub_elements:
            module_element.elements.append(_create_module_element(sub_block))

    return module_element
