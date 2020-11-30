from unittest import case
from pathlib import Path
from mdclasses.utils.path_resolver import get_path_resolver
from mdclasses.configuration_enums import Format, ObjectType


class TestPathResolverConfiguration(case.TestCase):

    def setUp(self) -> None:
        self.test_data_root = Path(Path(__file__).parent).joinpath('test_data', 'config')
        self.file_format = Format.CONFIGURATOR
        self.path_resolver = get_path_resolver(self.file_format)

    def test_config_file_path(self):
        paths = {
            'FilterCriteria': ObjectType.FILTER_CRITERION,
            'ChartsOfCharacteristicTypes': ObjectType.CHART_OF_CHARACTERISTIC_TYPES,
            'ChartsOfAccounts': ObjectType.CHART_OF_ACCOUNTS,
            'BusinessProcesses': ObjectType.BUSINESS_PROCESS,
            'ChartsOfCalculationTypes': ObjectType.CHART_OF_CALCULATION_TYPES,
            'Catalogs': ObjectType.CATALOG,

        }
        name = 'Test'

        for path in paths:
            test_path = self.path_resolver.conf_file_path(paths[path], name)
            self.assertEqual(test_path, Path(path).joinpath(f'{name}.xml'),
                             f'Для типа {paths[path]} не верно определен путь к файлу описанию.')

    def test_ext_path(self):
        name = 'test'
        paths = {
            'FilterCriteria': ObjectType.FILTER_CRITERION,
            'ChartsOfCharacteristicTypes': ObjectType.CHART_OF_CHARACTERISTIC_TYPES,
            'ChartsOfAccounts': ObjectType.CHART_OF_ACCOUNTS,
            'BusinessProcesses': ObjectType.BUSINESS_PROCESS,
            'ChartsOfCalculationTypes': ObjectType.CHART_OF_CALCULATION_TYPES,
            'Catalogs': ObjectType.CATALOG,

        }

        for path in paths:
            test_path = self.path_resolver.ext_path(paths[path], name)
            self.assertEqual(
                test_path,
                Path(path).joinpath(name).joinpath('Ext'),
                f'Для типа {paths[path]} не верно определен путь.'
            )

    def test_type_path(self):

        paths = {
            '': ObjectType.CONFIGURATION,
            'FilterCriteria': ObjectType.FILTER_CRITERION,
            'ChartsOfCharacteristicTypes': ObjectType.CHART_OF_CHARACTERISTIC_TYPES,
            'ChartsOfAccounts': ObjectType.CHART_OF_ACCOUNTS,
            'BusinessProcesses': ObjectType.BUSINESS_PROCESS,
            'ChartsOfCalculationTypes': ObjectType.CHART_OF_CALCULATION_TYPES,
            'Catalogs': ObjectType.CATALOG,

        }

        for path in paths:
            test_path = self.path_resolver.type_path(paths[path])
            self.assertEqual(test_path, Path(path), f'Для типа {paths[path]} не верно определен путь.')

    def test_form_path(self):

        types_without_forms = [
            ObjectType.CONFIGURATION,
            ObjectType.COMMAND_GROUP,
            ObjectType.COMMON_MODULE,
            ObjectType.COMMON_ATTRIBUTE,
            ObjectType.COMMON_PICTURE,
            ObjectType.COMMON_TEMPLATE
        ]

        for obj_type in types_without_forms:
            with self.assertRaises(ValueError) as ex:
                self.path_resolver.form_path(obj_type, 'form')
            self.assertIn(f'{obj_type}', ex.exception.args[0], 'Неожиданное иссключение.')

        constant_path = self.path_resolver.form_path(ObjectType.CONSTANT, 'Конст')
        self.assertEqual(constant_path, Path('CommonForms/ФормаКонстант'), 'Не верно определён путь к форме констант')

        comm_form__path = self.path_resolver.form_path(ObjectType.COMMON_FORM, 'Конст')
        self.assertEqual(comm_form__path, Path('CommonForms/Конст'), 'Не верно определен путь к общей форме')

        catalog_path = self.path_resolver.form_path(ObjectType.CATALOG, 'Конст', 'Form')
        self.assertEqual(catalog_path, Path('Catalogs/Конст/Forms/Form'),
                         'Не верно определена путь к форме справочника')