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



