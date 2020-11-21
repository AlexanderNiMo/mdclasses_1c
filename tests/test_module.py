from unittest import case
from pathlib import Path

from mdclasses.Module.Module import (create_module, ModuleParser, TextData,
                                     Region, Function, Procedure, PreprocessorInstruction, ModuleElement, Module)


test_module = './test_data/module/TestModule.bsl'


class TestModuleParser(case.TestCase):

    def get_test_module(self) -> Module:
        module_path = Path(test_module).absolute()
        parser = ModuleParser()
        return create_module(parser, module_path)

    def test_parse_module(self):
        module = self.get_test_module()
        text = module._path.read_text('utf-8-sig')

        types = [TextData, Region, Function, Procedure, PreprocessorInstruction]

        for val_type in types:
            for element in module.element_by_class(val_type):
                if self.emulate_change_module_element(element):
                    break

        self.assertEqual(module.changed, True, 'После изменения элемента флаг изменения в модуле долен быть взведен.')
        module_text = module.text

        self.assertEqual(text, module_text, 'Сгенерированный текст модуля должен быть идентичен исходному!')

        self.assertEqual(module.name, module._path.stem, 'Имя модуля определено не корректно')

        self.assertIsNotNone(module.elements[6].elements[15].elements[7].expansion_modifier,
                             'Не корректно определены модификаторы подпрограммы')

    def test_find_sub_program(self):
        module = self.get_test_module()

        sub_prog = module.find_sub_program('СообщитьПользователю')

        self.assertEqual(sub_prog.name, 'СообщитьПользователю', 'Не верно найдена процедура')
        self.assertIsInstance(sub_prog, Procedure, 'Не верно найдена процедура')

        sub_prog = module.find_sub_program('МакетСуществует')
        self.assertEqual(sub_prog.name, 'МакетСуществует', 'Не верно найдена функция')
        self.assertIsInstance(sub_prog, Function, 'Не верно найдена функция')

        with self.assertRaises(KeyError) as error:
            module.find_sub_program('СообщитьПользователю1111111')

        self.assertEqual(error.exception.args[0], 'В модуле нет подпрограммы СообщитьПользователю1111111.',
                         'Неожиданное исключение')

    def emulate_change_module_element(self, element: ModuleElement):
        result = True

        if isinstance(element, TextData):
            element.text_data = element.text_data
        elif isinstance(element, (Function, Procedure)):
            if element.name in ['ЗначенияРеквизитовОбъекта', 'УстановитьРабочуюДатуПользователя']:
                element.name = element.name
            else:
                 result = False
        elif isinstance(element, Region):
            element.name = element.name
        elif isinstance(element, PreprocessorInstruction):
            element.instruction_type = element.instruction_type

        return result

    def test_update_subprogramm(self):

        module = self.get_test_module()

        func = module.find_sub_program('ЗначенияРеквизитовОбъекта')
        last_element = func.elements[-1]
        new_line = '\taбырвалг = 1; \n'
        text_element = TextData(new_line, last_element.text_range.end_line+1, last_element.text_range.end_line+2)

        func.add_sub_element(text_element)

        module_text = module.text
        self.assertIn(new_line, module_text, 'не обнаруженна добавленная строка!')
