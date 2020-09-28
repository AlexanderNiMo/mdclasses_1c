from os import path
import re
from mdclasses.conf_base import ObjectType
from lxml.etree import parse, QName, ElementTree
from typing import Dict


class XMLParser:

    def __init__(self, file: str, obj_type: ObjectType):
        self.file = path.abspath(file)
        self.obj_type = obj_type

    def _get_childs(self, obj: ElementTree):
        return obj.xpath('./tns:ChildObjects/*', namespaces={'tns': obj.nsmap[None]})

    def _get_uuid(self, obj: ElementTree):
        return obj.attrib['uuid']

    def _get_property(self, obj: ElementTree, tag_name: str):
        return obj.xpath(f'./tns:Properties/tns:{tag_name}', namespaces={'tns': obj.nsmap[None]})

    def parse_configuration(self):

        configuration = self._get_root()

        childes = []
        uuid = self._get_uuid(configuration)
        name_obj = self._get_property(configuration, 'Name')[0]
        name = name_obj.text

        child_objs = self._get_childs(configuration)

        for child_obj in child_objs:
            childes.append(dict(
                obj_type=QName(child_obj).localname,
                obj_name=child_obj.text,
                line_number=child_obj.sourceline
            ))

        return uuid, childes, name

    def parse_object(self):

        obj = self._get_root()

        childes = dict(
            attributes=list(),
            forms=list(),
            templates=list(),
            commands=list(),
        )
        uuid = self._get_uuid(obj)
        child_objs = self._get_childs(obj)
        name_obj = self._get_property(obj, 'Name')[0]

        if self.obj_type in [
            ObjectType.SUBSYSTEM,
        ]:
            return uuid, childes, name_obj.sourceline

        for child_obj in child_objs:
            self.set_child_by_tag(childes, child_obj)

        return uuid, childes, name_obj.sourceline

    def set_child_by_tag(self, childes: Dict[str, list], obj: ElementTree):
        tag = QName(obj).localname
        if tag == 'Form':
            pass
        elif tag == 'Template':
            pass
        elif tag == 'Command':
            pass
        elif tag in ['Attribute', 'Operation', 'Column',
                     'EnumValue', 'Resource', 'Dimension',
                     'AccountingFlag', 'ExtDimensionAccountingFlag', 'AddressingAttribute']:
            childes['attributes'].append(self._parse_attr_child(obj))
        elif tag in ['TabularSection', 'URLTemplate']:
            tabular_data = self._parse_attr_child(obj)
            tabular_data['attributes'] = [self._parse_attr_child(tab_attr) for tab_attr in self._get_childs(obj)]
            childes['attributes'].append(tabular_data)
        else:
            raise ValueError(f'Не описан tag {tag}')

    def _parse_attr_child(self, obj: ElementTree):
        name_obj = self._get_property(obj, 'Name')[0]
        return dict(
            uuid=self._get_uuid(obj),
            name=name_obj.text,
            line_number=name_obj.sourceline
        )

    def _get_root(self) -> ElementTree():

        with open(self.file, r'r', encoding='utf-8') as f:
            tree = parse(f)

        root = tree.getroot()

        obj_tag = root.xpath(f'//tns:{self.obj_type.value}', namespaces={'tns': root.nsmap[None]})

        if len(obj_tag) == 0:
            raise ValueError(f'Не найден объект по типу {self.obj_type.value} в файле {self.file}')
        obj_tag = obj_tag[0]

        return obj_tag


class SupportConfigurationParser:
    REG_EXP = r'(?:,|\\n|^)(\"(?:(?:\"\")*[^\"]*)*\"|[^\",\\n]*|(?:\\n|$))'

    FILE_CONF_NUMBER = 2

    CONF_VERSION_SHIFT = 3
    CONF_PROVIDER_SHIFT = 4
    CONF_NAME_SHIFT = 5
    CONF_OBJECTS_SHIFT = 6

    OBJECT_TUPLE_LEN = 4
    OBJECT_SUPPORT_TYPE_SHIFT = 0
    OBJECT_UUID_SHIFT = 2

    '''
    Описание формата по позиции в картеже описании элемента:
        0 - support_type;
        2 - UUID элмента 
    '''

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> dict:
        conf_data = {}
        with open(self.file_path, r'r', encoding='utf-8-sig') as f:
            data = f.read()

            file_reg_exp = re.compile(self.REG_EXP)
            file_data = file_reg_exp.findall(data)

            cur_element = 3
            cur_configuration = int(file_data[self.FILE_CONF_NUMBER])

            for conf_number in range(cur_configuration):

                conf_version = file_data[cur_element+self.CONF_VERSION_SHIFT]
                conf_provider = file_data[cur_element+self.CONF_PROVIDER_SHIFT]
                conf_name = file_data[cur_element+self.CONF_NAME_SHIFT].replace('"', '')
                cur_conf_objects = int(file_data[cur_element+self.CONF_OBJECTS_SHIFT])
                conf_objects = {}

                for object_num in range(
                        cur_element + 1 + self.CONF_OBJECTS_SHIFT,
                        cur_element + self.CONF_OBJECTS_SHIFT + cur_conf_objects * self.OBJECT_TUPLE_LEN,
                        self.OBJECT_TUPLE_LEN):
                    object_support_type = int(file_data[object_num + self.OBJECT_SUPPORT_TYPE_SHIFT])
                    object_uuid = file_data[object_num + self.OBJECT_UUID_SHIFT]
                    conf_objects[object_uuid] = object_support_type

                cur_element = object_num + 2 + self.OBJECT_TUPLE_LEN

                conf_data[conf_name] = dict(
                    conf_version=conf_version,
                    conf_provider=conf_provider,
                    conf_objects=conf_objects,
                )

        return conf_data