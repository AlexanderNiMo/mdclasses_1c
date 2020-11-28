from unittest import case
from pathlib import Path
from json import dumps, load
import shutil
import tempfile
import os

from mdclasses.builder import create_configuration, read_configuration_objects, read_configuration
from mdclasses import ObjectType, ConfObject, Configuration, Module

test_data_root = Path(Path(__file__).parent).joinpath('test_data', 'config')
json_report_path = Path(Path(__file__).parent).joinpath('test_data', 'json_data', 'report.json')
json_config_path = Path(Path(__file__).parent).joinpath('test_data', 'json_data', 'configuration_not_full.json')

encoding = 'utf-8'


class TestConfiguration(case.TestCase):

    def test_read_configuration(self):

        conf_path = Path(test_data_root).absolute()

        conf = create_configuration(conf_path)

        self.assertEqual(conf.name, 'Конфигурация', 'Не верно определено имя конфигурации.')
        self.assertEqual(conf.uuid, '04e5fb66-c0ac-4f0b-8a97-f8f51ce50450', 'Не верно определен uuid конфигурации')
        self.assertEqual(
            conf.root_path,
            conf_path,
            'Не верно установлен корень конфигурации'
        )

        self.assertEqual(len(conf.conf_objects), 45, 'Не корректно загружен состав объектов.')

        report = conf.get_object('Отчет1', ObjectType.REPORT)

        self.assertTupleEqual(
            (report.name, report.obj_type),
            ('Отчет1', ObjectType.REPORT),
            'Не корректно найден объект.'
        )

        with self.assertRaises(IndexError, msg='Объекта "Отчет112" нет в конфигурации должно ожидали ошибку') as _:
            conf.get_object('Отчет11', ObjectType.REPORT)

        self.assertEqual(
            dumps(conf.to_dict(), ensure_ascii=False),
            Path(json_config_path).read_text(encoding=encoding),
            'Конфигурация не верно сериализована'
        )

    def test_read_configuration_object(self):
        conf_path = Path(test_data_root).absolute()

        conf = create_configuration(conf_path)
        read_configuration_objects(conf)

        report = conf.get_object('Отчет1', ObjectType.REPORT)

        self.assertEqual(
            report.name,
            'Отчет1',
            'Объект имеет неожиданное имя.')

        self.assertEqual(
            report.obj_type,
            ObjectType.REPORT,
            'Объект имеет неожиданный тип.')

        self.assertEqual(
            report.line_number,
            15,
            'Не верно определена строка в файле')

        self.assertEqual(
            report.relative_path,
            'Reports/Отчет1.xml',
            'Не верно определена строка в файле')

        self.assertEqual(report.full_name, 'Report.Отчет1', 'Не верно определено имя')

        self.assertEqual(
            dumps(report.to_dict(), ensure_ascii=False),
            Path(json_report_path).read_text(encoding=encoding),
            'Объект не верно сериализован')

    def test_read_props(self):
        pass

    def test_read_obj_module(self):
        conf_path = Path(test_data_root).absolute()

        conf = create_configuration(conf_path)
        read_configuration_objects(conf)

        doc = conf.get_object('Документ1', ObjectType.DOCUMENT)
        doc.read_modules()

        self.assertEqual(len(doc.modules), 2, 'не все модули были прочитаны.')

    def test_read_forms(self):
        conf_path = Path(test_data_root).absolute()

        conf = create_configuration(conf_path)
        read_configuration_objects(conf)

        doc = conf.get_object('Документ1', ObjectType.DOCUMENT)
        doc.read_forms()
        self.assertEqual(len(doc.forms), 1, 'не все формы были прочитаны.')

        self.assertIsInstance(doc.forms[0].module, Module, 'Модуль не прочитан')

    def read_empty_form(self):
        conf_path = Path(test_data_root).absolute()
        conf = read_configuration(conf_path)

        filter = conf.get_object('HTTPСервис1', ObjectType.HTTP_SERVICE)
        filter.read_forms()

    def test_ext_path(self):
        conf_path = Path(test_data_root).absolute()
        conf = read_configuration(conf_path)

        obj = conf.get_object('Форма', ObjectType.COMMON_FORM)
        self.assertEqual(conf_path.joinpath('CommonForms', 'Форма', 'Ext'), obj.ext_path,
                         'Не верно определен путь ext для COMMON_FORM')

        obj = conf.get_object('Перечисление1', ObjectType.ENUM)
        self.assertEqual(conf_path.joinpath('Enums', 'Перечисление1', 'Ext'), obj.ext_path,
                         'Не верно определен путь ext для Enums')

    def test_form_path(self):
        conf_path = Path(test_data_root).absolute()
        conf = read_configuration(conf_path)

        obj = conf.get_object('Форма', ObjectType.COMMON_FORM)
        self.assertEqual(conf_path.joinpath('CommonForms', 'Форма', 'Ext'), obj.form_path,
                         'Не верно определен путь ext для COMMON_FORM')

        obj = conf.get_object('Документ1', ObjectType.DOCUMENT)
        self.assertEqual(conf_path.joinpath('Documents', 'Документ1', 'Forms'), obj.form_path,
                         'Не верно определен путь ext для Enums')

    def read_empty_module(self):
        conf_path = Path(test_data_root).absolute()
        conf = read_configuration(conf_path)

        filter = conf.get_object('КритерийОтбора1', ObjectType.FILTER_CRITERION)
        filter.read_modules()

    def test_read_all_configuration(self):
        conf_path = Path(test_data_root).absolute()
        read_configuration(conf_path)

    def test_from_json(self):
        with Path(json_config_path).open('r', encoding=encoding) as f:
            conf = Configuration.from_dict(load(f))
        with Path(json_report_path).open('r', encoding=encoding) as f:
            report = ConfObject.from_dict(load(f), conf)


class TestChangeConfiguration(case.TestCase):

    def setUp(self) -> None:
        self.temp_path = test_data_root.parent.joinpath('temp').resolve().absolute()
        self.temp_config_path = self.temp_path.joinpath('config').resolve().absolute()
        self.base_config_path = self.temp_path.joinpath('config_base').resolve().absolute()
        if not self.temp_path.exists():
            self.temp_path.mkdir()
        shutil.copytree(test_data_root, self.temp_config_path)
        shutil.copytree(test_data_root, self.base_config_path)

    def test_save_configuration(self):
        conf = read_configuration(self.temp_config_path)

        conf.conf_objects.append(ConfObject('test', ObjectType.REPORT, conf))
        conf.conf_objects.append(ConfObject('test1', ObjectType.DOCUMENT, conf))

        tmp_file = tempfile.mktemp()
        shutil.copy(Path(conf.file_name), Path(tmp_file))

        conf.save_to_file()
        self.assertIn('<Report>test</Report>', Path(conf.file_name).read_text(encoding='utf-8'))
        self.assertIn('<Document>test1</Document>', Path(conf.file_name).read_text(encoding='utf-8'))
        os.remove(Path(conf.file_name))
        shutil.copy(Path(tmp_file), Path(conf.file_name))
        os.remove(Path(tmp_file))

    def test_clone_obj(self):
        conf_base = read_configuration(self.base_config_path)
        filter = conf_base.get_object('КритерийОтбора1', ObjectType.FILTER_CRITERION)

        conf = read_configuration(self.temp_config_path)
        with self.assertRaises(ValueError) as ex:
            conf.add_object(filter)
        self.assertEqual(ex.exception.args[0], f'Объект {filter} уже есть в конфигурации')

        dir_path = filter.obj_dir
        file_name = filter.file_name
        filter.name = 'КритерийОтбора2'

        shutil.copytree(dir_path, filter.obj_dir)
        shutil.copy(file_name, filter.file_name)

        new_object = conf.add_object(filter)

        self.assertTrue(new_object.obj_dir.exists(), 'Данные объекта не перенесены')

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_path)
