import re
from typing import Dict, List, Optional, Union


class ModuleParser:

    RegionDataRegExp = re.compile(r'^( |\t)*#Область\s*(?P<region_name>.*$)', flags=re.MULTILINE | re.IGNORECASE)

    PreprocessorDataRegExp = re.compile(
        r'^( |\t)*#Если\s*(?P<preprocessor_type>[А-Яа-я \t]*)\s*Тогда',
        flags=re.MULTILINE | re.IGNORECASE
    )

    SubProgramDeclarationRegExp = re.compile(
        r'(?P<Comment>(^[ \t]*\/\/(.| |\t)*$\n)*)?(?P<Preproc>(^[ \t]*&[^)(]*$\n))?(?P<ExtensionParam>(^[ \t]*&.*$\n)*)?^[ \t]*(?P<type>Процедура|Функция)[ \t]*(?P<name>[\wа-яА-Я1-9]*)\((?P<Params>(((Знач)?\s?[^,\n)]*),?\s?)+?)\)(?P<Public>[ |\t]Экспорт)?',
        flags=re.MULTILINE | re.IGNORECASE
    )

    ParamsRegExp = re.compile(
        r'((?P<by_value>Знач)?( |\t)*(?P<Param>[^,\n)=]*)=?( |\t)*(?P<default>[^,\n)]*)),?\s?',
        flags=re.MULTILINE | re.IGNORECASE
    )

    ExtensionDefenition = re.compile(
        r'^( |\t)*&(?P<Directive>[^(]*)\(\"(?P<SubProgramName>[^\"]*)',
        flags=re.MULTILINE | re.IGNORECASE
    )

    Directive = re.compile(
        r'^( |\t)*&(?P<Directive>[^\n(]*)$',
        flags=re.MULTILINE | re.IGNORECASE
    )

    def parse_module_text(self, text: str) -> 'ModuleBlock':

        module_block = self.get_module_blocks(text)

        self.parse_block(module_block)

        self.parse_sub_programs(module_block)

        return module_block

    def get_module_blocks(self, text: str) -> 'ModuleBlock':

        text_parser = TextLineParser(text)
        return text_parser.get_module_blocks()

    def parse_block(self, block: 'ModuleBlock'):

        try:
            if block.block_type == 'preprocessor':
                data = self.PreprocessorDataRegExp.search(block.text).groupdict()
                block.add_data('preprocessor_type', data['preprocessor_type'].strip())
            elif block.block_type == 'region':
                data = self.RegionDataRegExp.search(block.text).groupdict()
                block.add_data('name', data['region_name'])
            elif block.block_type == 'sub_program' and not self.full_sub_program_declaration(block.text):
                self.extend_sub_program_block(block)
        except AttributeError as ex:
            raise AttributeError(f'При чтении блока типа {block.block_type} с текстом {block.text} произошла ошибка {ex}')

        removing_blocks = []
        block.sub_elements.reverse()
        prev_block = None
        for sub_block in block.sub_elements:
            if self.expanding_block(sub_block, prev_block):
                prev_block.expand_block(sub_block, True)
                removing_blocks.append(sub_block)
            else:
                self.parse_block(sub_block)
                prev_block = sub_block

        for r_block in removing_blocks:
            block.sub_elements.remove(r_block)

        block.sub_elements.reverse()

    def extend_sub_program_block(self, block):
        removing_blocks = []
        for sub_block in block.sub_elements:
            if self.full_sub_program_declaration(block.text):
                break
            lines = sub_block.text.splitlines(True)
            line_number = 0
            for line_number, sub_line in enumerate(lines):
                if self.full_sub_program_declaration(block.text):
                    break
                else:
                    block.add_text(sub_line.rstrip())
            sub_block.text = ''.join(lines[line_number:])
            if sub_block.text == '':
                removing_blocks.append(sub_block)
        for r_block in removing_blocks:
            block.sub_elements.remove(r_block)

    def expanding_block(self, sub_block: 'ModuleBlock', previous_block: 'ModuleBlock'):
        if previous_block is None:
            return False

        expand_block_types = ['comment', 'preproc']
        expandable_block_type = ['sub_program']

        return sub_block.block_type in expand_block_types and previous_block.block_type in expandable_block_type

    def parse_sub_programs(self, block):
        for sub_programm in block.blocks_by_type('sub_program'):

            data = self.SubProgramDeclarationRegExp.search(sub_programm.text).groupdict()

            sub_programm.add_data('name', data['name'])
            sub_programm.add_data('type', data['type'])
            sub_programm.add_data('comment', data['Comment'])

            if data['Preproc'] == '' or data['Preproc'] is None:
                preproc = None
            else:
                preproc = self.Directive.search(data['Preproc']).groupdict()

            sub_programm.add_data('preproc', preproc)

            if data['ExtensionParam'] == '' or data['ExtensionParam'] is None:
                extension = None
            else:
                extension = self.ExtensionDefenition.search(data['ExtensionParam']).groupdict()

            sub_programm.add_data('extension', extension)

            params = self.parse_param_text(data['Params'])
            sub_programm.add_data('params', params)

            sub_programm.add_data('public', False if data['Public'] == '' or data['Public'] is None else True)

    def parse_param_text(self, param_text: str) -> List[Dict[str, str]]:

        params = []

        params_text = param_text.replace('\n', '')

        for split_param in self.ParamsRegExp.finditer(params_text):
            data = split_param.groupdict()
            if data['Param'] is None or data['Param'] == '':
                continue
            params.append(
                dict(
                    name=data['Param'],
                    by_value=False if data['by_value'] is None else True,
                    default_value=None if data['default'] == '' or data['default'] is None else data['default']
                )
            )
            f=1

        return params

    def full_sub_program_declaration(self, declaration_text):
        return ')' in declaration_text


class TextLineParser:

    RegionStartRegExp = re.compile(
        r'#Область',
        flags=re.MULTILINE | re.IGNORECASE
    )
    RegionEndRegExp = re.compile(
        r'#КонецОбласти',
        flags=re.MULTILINE | re.IGNORECASE
    )

    PreprocessorStart = re.compile(
        r'#Если(.*\s)',
        flags=re.MULTILINE | re.IGNORECASE
    )

    PreprocessorEnd = re.compile(
        r'#КонецЕсли',
        flags=re.MULTILINE | re.IGNORECASE
    )

    SubProgramStart = re.compile(
        r'Процедура|Функция',
        flags=re.MULTILINE | re.IGNORECASE
    )

    SubProgramEnd = re.compile(
        r'КонецФункции|КонецПроцедуры',
        flags=re.MULTILINE | re.IGNORECASE
    )

    Comment = re.compile(
        r'^[ \t]*\/\/(.| |\t)*',
        flags=re.MULTILINE | re.IGNORECASE
    )

    Preproc = re.compile(
        r'^[ \t]*&.*$',
        flags=re.MULTILINE | re.IGNORECASE
    )

    def __init__(self, text: str):
        self.current_level: int = 0
        self.root: ModuleBlock = ModuleBlock(level=0, block_type='module', start=0, text=text)
        self.__lines: List[str] = text.splitlines(keepends=True)
        self.current_root: ModuleBlock = self.root
        self.text_data_cache: dict = {'text': None, 'comment': None, 'preproc': None}
        self.line_number: int = 0

    def get_module_blocks(self) -> 'ModuleBlock':

        if len(self.__lines) == 0:
            return self.root

        for line in self.lines:

            line_type = self.get_line_type(line)

            if not self.text_data_line(line_type):
                self.clear_text_cache_data()

            if self.start_area_type(line_type):

                if self.current_root.block_type == 'sub_program':
                    # Внутри процедур и функция не обрабатываем области и препроцессоры на этом этапе
                    # добавим как текст
                    self.handle_text_data('text', line)
                    continue
                self.handle_start_area_block(line_type, line)

            elif self.close_area_type(line_type):

                if self.current_root.block_type == 'sub_program' and line_type != 'sub_program__end':
                    # Внутри процедур и функция не обрабатываем области и препроцессоры на этом этапе
                    # добавим как текст
                    self.handle_text_data('text', line)
                    continue
                self.handle_close_area_block(line)

            else:
                self.handle_text_data(line_type, line)

        self.clear_text_cache_data()

        if self.root.text[-1] == '\n':
            self.add_last_line()

        self.root.end = self.line_number

        return self.root

    def add_last_line(self):
        last_element = self.root.sub_elements[-1]
        if self.text_data_line(last_element.block_type):
            last_element.text += '\n'
        elif last_element.block_type in ['region', 'preprocessor', 'sub_program']:
            data = last_element.get_data()
            data['ent_text'] += '\n'
            last_element.add_data('ent_text', data['ent_text'])

    def handle_start_area_block(self, line_type, line):
        self.current_level += 1

        block_type = line_type.split('__')[0]

        data = ModuleBlock(
            level=self.current_level,
            block_type=block_type,
            start=self.line_number,
            text=line,
            root=self.current_root
        )
        self.current_root.sub_elements.append(data)
        self.current_root = data

    def handle_close_area_block(self, line: str):
        self.current_level -= 1
        self.current_root.end = self.line_number
        self.current_root.add_data('ent_text', line)
        self.current_root = self.current_root.root

    def handle_text_data(self, line_type, line):
        self.clear_text_cache_data(line_type)
        value = line
        self.add_text_data_to_chache(line=value, line_type=line_type)

    def get_line_type(self, line: str) -> str:
        block_types: Dict[str, re.Pattern] = dict(
            region__start=self.RegionStartRegExp,
            region__end=self.RegionEndRegExp,
            preprocessor__start=self.PreprocessorStart,
            preprocessor__end=self.PreprocessorEnd,
            sub_program__start=self.SubProgramStart,
            sub_program__end=self.SubProgramEnd,
            comment=self.Comment,
            preproc=self.Preproc,
        )

        for k, v in block_types.items():
            if v.match(line):
                return k

        return 'text'

    @property
    def lines(self):
        for line_number, line in enumerate(self.__lines):
            self.line_number = line_number
            yield line.replace('\n', '')

    def clear_text_cache_data(self, exept_key: Optional[str] = None):
        for key in self.text_data_cache.keys():
            if exept_key is not None and key == exept_key:
                continue
            if self.text_data_cache[key] is not None:
                self.text_data_cache[key].end = self.line_number - 1
                self.text_data_cache[key] = None

    def get_text_data_from_cache(self, line_type: str):
        data = self.text_data_cache[line_type]
        if data is None:
            self.text_data_cache[line_type] = ModuleBlock(
                level=self.current_level,
                block_type=line_type,
                start=self.line_number,
                root=self.current_root
            )
            self.current_root.sub_elements.append(self.text_data_cache[line_type])
        return self.text_data_cache[line_type]

    def add_text_data_to_chache(self, line_type, line):
        self.get_text_data_from_cache(line_type)
        self.text_data_cache[line_type].add_text(line)

    def text_data_line(self, line_type) -> bool:
        return line_type in ['text', 'comment', 'preproc']

    def sub_program_line(self, line_type):
        return line_type in ['sub_program__start', 'sub_program__end']

    def start_area_type(self, line_type):
        return line_type in ['region__start', 'preprocessor__start', 'sub_program__start']

    def close_area_type(self, line_type):
        return line_type in ['region__end', 'preprocessor__end', 'sub_program__end']


class ModuleBlock:

    def __init__(self, level: int,
                 block_type: str,
                 start: int,
                 text: Optional[str] = None,
                 root: Optional['ModuleBlock'] = None,
                 sub_elements: list = None,
                 end: Optional[int] = None):
        self.end: int = end
        self.start: int = start
        self.sub_elements: List['ModuleBlock'] = list() if sub_elements is None else sub_elements
        self.root:'ModuleBlock' = root
        self.block_type: str = block_type
        self.level: int = level
        self.text: str = text

        self.__aditional_data = {}

    def add_data(self, name: str, data: Union[dict, str]):
        self.__aditional_data[name] = data

    def add_text(self, text, to_the_begining=False):
        delimiter = "" if self.text is None else "\n"
        self.text = '' if self.text is None else self.text
        if to_the_begining:
            self.text = f'{text}{delimiter}{self.text}'
        else:
            self.text += f'{delimiter}{text}'

    def expand_block(self, expanding: 'ModuleBlock', to_the_begining=False):
        self.add_text(expanding.text, to_the_begining)
        if to_the_begining:
            self.start = expanding.start
        else:
            self.end = expanding.end

    def blocks_by_type(self, block_type: str):
        if self.block_type == block_type:
            yield self
        for sub_block in self.sub_elements:
            for type_block in sub_block.blocks_by_type(block_type):
                yield type_block

    def get_data(self):
        return self.__aditional_data

    def __repr__(self):
        return f'<ModuleBlock: {self.block_type} {self.start}:{self.end}>'

