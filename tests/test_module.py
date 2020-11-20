from unittest import case
from pathlib import Path

from mdclasses.Module.Module import (create_module, ModuleParser, TextData,
                                     Region, Function, Procedure, PreprocessorInstruction, ModuleElement)


test_module = './test_data/module/Module.bsl'


class TestModuleParser(case.TestCase):

    def test_parse_module(self):

        module_path = Path(test_module).absolute()
        parser = ModuleParser()

        module = create_module(parser, module_path)
        text = module_path.read_text('utf-8-sig')

        types = [TextData, Region, Function, Procedure, PreprocessorInstruction]

        for val_type in types:
            for element in module.element_by_class(val_type):
                if self.emulate_change_module_element(element):
                    break

        self.assertEqual(module.changed, True, 'После изменения элемента флаг изменения в модуле долен быть взведен.')
        module_text = module.text

        self.assertEqual(text, module_text, 'Сгенерированный текст модуля должен быть идентичен исходному!')

        self.assertEqual(module.name, module_path.stem, 'Имя модуля определено не корректно')

        self.assertIsNotNone(module.elements[6].elements[15].elements[7].expansion_modifier, 'Не корректно определены модификаторы подпрограммы')

    def test_find_sub_program(self):
        module_path = Path(test_module).absolute()
        parser = ModuleParser()
        module = create_module(parser, module_path)

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



