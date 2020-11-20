from unittest import case
from pathlib import Path
from json import dumps, load

from mdclasses.builder import create_configuration, read_configuration_objects
from mdclasses import ObjectType, ConfObject, Configuration, Module

test_data_root = './test_data/config'
json_report_path = './test_data/json_data/report.json'
json_config_path = './test_data/json_data/configuration_not_full.json'

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
            'Объект не верно сериализован'
        )

    def test_from_json(self):
        with Path(json_config_path).open('r', encoding=encoding) as f:
            conf = Configuration.from_dict(load(f))
        with Path(json_report_path).open('r', encoding=encoding) as f:
            report = ConfObject.from_dict(load(f), conf)
