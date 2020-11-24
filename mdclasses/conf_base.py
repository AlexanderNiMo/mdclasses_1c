from typing import List, Dict, Union
import enum
from os import path
from pathlib import Path
from abc import ABC, abstractmethod

from mdclasses.Module import Module, create_module, ModuleParser
from mdclasses.Form import Form


class ObjectType(enum.Enum):
    UNDEFINED = ''
    CONFIGURATION = 'Configuration'
    INFORMATION_REGISTER = "InformationRegister"
    FUNCTIONAL_OPTION = "FunctionalOption"
    STYLE_ITEM = "StyleItem"
    CONSTANT = "Constant"
    COMMON_MODULE = "CommonModule"
    DEFINED_TYPE = "DefinedType"
    CHART_OF_CHARACTERISTIC_TYPES = "ChartOfCharacteristicTypes"
    SCHEDULED_JOB = "ScheduledJob"
    XDTO_PACKAGE = "XDTOPackage"
    LANGUAGE = "Language"
    COMMON_TEMPLATE = "CommonTemplate"
    COMMAND_GROUP = "CommandGroup"
    REPORT = "Report"
    ROLE = "Role"
    WEBSERVICE = "WebService"
    CATALOG = "Catalog"
    SESSION_PARAMETER = "SessionParameter"
    INTERFACE = "Interface"
    DOCUMENT = "Document"
    DOCUMENT_JOURNAL = "DocumentJournal"
    EXCHANGE_PLAN = "ExchangePlan"
    DATA_PROCESSOR = "DataProcessor"
    COMMON_COMMAND = "CommonCommand"
    COMMON_PICTURE = "CommonPicture"
    STYLE = "Style"
    FILTER_CRITERION = "FilterCriterion"
    SUBSYSTEM = "Subsystem"
    FUNCTIONAL_OPTIONS_PARAMETER = "FunctionalOptionsParameter"
    ENUM = "Enum"
    COMMON_FORM = "CommonForm"
    SETTINGS_STORAGE = "SettingsStorage"
    EVENT_SUBSCRIPTION = "EventSubscription"
    COMMON_ATTRIBUTE = 'CommonAttribute'
    HTTP_SERVICE = 'HTTPService'
    WS_REFERENCE = 'WSReference'
    DOCUMENT_NUMERATOR = 'DocumentNumerator'
    SEQUENCE = 'Sequence'
    ACCUMULATION_REGISTER = 'AccumulationRegister'
    CHART_OF_ACCOUNTS = 'ChartOfAccounts'
    ACCOUNTING_REGISTER = 'AccountingRegister'
    BUSINESS_PROCESS = 'BusinessProcess'
    TASK = 'Task'
    CHART_OF_CALCULATION_TYPES = 'ChartOfCalculationTypes'
    CALCULATION_REGISTER = 'CalculationRegister'
    EXTERNAL_DATA_SOURCE = 'ExternalDataSource'
    DIMENSION_TABLE = 'DimensionTable'
    RECALCULATION = 'Recalculation'
    FORM = 'Form'
    TEMPLATE = 'Template'
    MODULE = 'Module'
    COMMAND = 'Command'
    TABLE = 'Table'
    CUBE = 'Cube'


class Serializable(ABC):

    @abstractmethod
    def to_dict(self):
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, args, kwargs):
        pass
    

class Supportable(Serializable):

    def __init__(self, uuid: str = ''):
        self.uuid = uuid
        self.support_type = SupportType.NONE_SUPPORT

    def set_support(self, support: dict):
        try:
            self.support_type = SupportType(support[self.uuid])
        except KeyError:
            self.support_type = SupportType.NONE_SUPPORT

    @property
    def on_support(self) -> bool:
        return self.support_type in [
            SupportType.NOT_EDITABLE,
            SupportType.EDITABLE_SUPPORT_ENABLED,
            SupportType.NOT_SUPPORTED
        ]
    
    def to_dict(self):
        return dict(
            uuid=self.uuid,
            support_type=self.support_type.value
        )

    @classmethod
    def from_dict(cls, *args, **kwargs):
        data = args[0] if 'data' not in kwargs else kwargs['data']

        obj = cls(data['uuid']) if 'obj' not in kwargs else kwargs['obj']

        obj.uuid = data['uuid']
        obj.set_support(data['support_type'])


class ConfObject(Supportable):

    def __init__(self, name: str, obj_type: Union[ObjectType, str], parent: 'Configuration', line_number: int=0):
        super(ConfObject, self).__init__()

        self.line_number = line_number

        self.parent = parent
        self.name = name

        self.modules: List[Module] = list()

        if isinstance(obj_type, str):
            self.obj_type = ObjectType(obj_type)
        else:
            self.obj_type = obj_type

        self.forms: List[Form] = list()
        self.templates = list()
        self.commands = list()
        self.attributes: List[ObjectAttribute] = list()

    @property
    def file_name(self):
        return path.join(self.root_path, self.relative_path)

    @property
    def full_name(self):
        return f'{self.obj_type.value}.{self.name}'

    @property
    def root_path(self):
        return self.parent.root_path

    @property
    def relative_path(self):
        return resolve_path(self.obj_type, self.name)

    @property
    def obj_dir(self) -> Path:
        return Path(self.file_name).parent

    @property
    def form_path(self):
        root_path = Path(self.root_path)
        return root_path.joinpath(resolve_form_path(self.obj_type, self.name))

    @property
    def ext_path(self) -> Path:
        root_path = Path(self.root_path)
        return root_path.joinpath(resolve_ext_path(self.obj_type, self.name)).absolute()

    def read_modules(self):
        ext_path = self.ext_path

        if not ext_path.exists():
            return

        parser = ModuleParser()

        for element in ext_path.iterdir():
            if element.is_file() and element.suffix == '.bsl':
                self.modules.append(create_module(parser, element))

    def read_forms(self):
        self.forms = []

        root_path = Path(self.root_path)

        forms_path = root_path.joinpath(resolve_form_path(self.obj_type, self.name)).absolute()

        if not forms_path.exists():
            return

        forms = {}

        for element in forms_path.iterdir():
            if element.is_file() and element.suffix == '.xml':
                name = element.stem
                if name in forms:
                    forms[name]['description_path'] = element
                else:
                    forms[name] = dict(description_path=element, structure_path='')
            elif element.is_dir():
                struct_path = element.joinpath('Ext', 'Form', 'Form.xml')
                name = element.stem
                if name in forms:
                    forms[name]['structure_path'] = struct_path
                else:
                    forms[name] = dict(description_path='', structure_path=struct_path)

        self.forms.extend(
            [Form(**v) for v in forms.values()]
        )

    def set_support(self, support: dict):

        super(ConfObject, self).set_support(support)

        for form in self.forms:
            form.set_support(support)

        for template in self.templates:
            template.set_support(support)

        for command in self.commands:
            command.set_support(support)

        for attribute in self.attributes:
            attribute.set_support(support)

    def set_childes(self, childes: Dict[str, list]):
        self.set_attributes(childes['attributes'])
        self.set_forms(childes['forms'])
        self.set_templates(childes['templates'])
        self.set_commands(childes['commands'])

    def set_forms(self, forms):
        pass

    def set_templates(self, templates):
        pass

    def set_commands(self, commands):
        pass

    def set_attributes(self, attributes: List[dict]):
        for attr_data in attributes:
            self.attributes.append(ObjectAttribute.from_dict(attr_data, self))

    def to_dict(self):
        data = super(ConfObject, self).to_dict()
        data.update(
            dict(
                name=self.name,
                obj_type=self.obj_type.value,
                attributes=[attr.to_dict() for attr in self.attributes],
                forms=[form.to_dict() for form in self.forms],
                templates=[template.to_dict() for template in self.templates],
                commands=[command.to_dict() for command in self.commands],
                line_number=self.line_number,
            )
        )
        return data

    @classmethod
    def from_dict(cls, data, parent: 'Configuration'):
        obj = cls(
            name=data['name'],
            parent=parent,
            line_number=data['line_number'],
            obj_type=data['obj_type'],
        )

        obj.uuid = data['uuid'],
        obj.set_childes(data)
        return obj

    def __repr__(self):
        return f'<ConfObject: {self.full_name}>'


class ObjectAttribute(Supportable):

    def __init__(self, name: str, uuid: str, parent: Union[ConfObject, 'ObjectAttribute'], line_number: int):
        super(ObjectAttribute, self).__init__(uuid)
        self.parent: Union[ConfObject, 'ObjectAttribute'] = parent
        self.name: str = name
        self.attributes: List[ObjectAttribute] = list()
        self.line_number: int = line_number

    def set_attributes(self, attributes: List[dict]):
        for attr_data in attributes:
            self.attributes.append(self.from_dict(attr_data, self))

    @property
    def file_name(self):
        return self.parent.file_name

    @property
    def full_name(self):
        return f'{self.parent.full_name}.{self.name}'

    def set_support(self, support: dict):
        super(ObjectAttribute, self).set_support(support)

        for attr in self.attributes:
            attr.set_support(support)

    @classmethod
    def from_dict(cls, attr_data: dict, parent: Union[ConfObject, 'ObjectAttribute']) -> 'ObjectAttribute':
        attr = cls(
            name=attr_data['name'],
            uuid=attr_data['uuid'],
            parent=parent,
            line_number=attr_data['line_number']
        )
        if 'attributes' in attr_data:
            attr.set_attributes(attr_data['attributes'])
        return attr

    def to_dict(self):
        data = super(ObjectAttribute, self).to_dict()
        data.update(
            dict(
                name=self.name,
                attributes=[attr.to_dict() for attr in self.attributes],
                line_number=self.line_number
            )
        )
        return data

    @property
    def root_path(self):
        return self.parent.root_path

    def __repr__(self):
        return f'<ObjectAttribute: {self.parent}.{self.name}>'


class Configuration(Supportable):

    def __init__(self, uuid: str, conf_objects: List[dict], root_path: str, name: str):
        super(Configuration, self).__init__(uuid)

        self.name = name
        self.root_path = root_path

        self.conf_objects = [
            ConfObject(
                name=conf_obj['obj_name'],
                obj_type=conf_obj['obj_type'],
                parent=self
            ) for conf_obj in conf_objects
        ]
        self.support_type = SupportType.NONE_SUPPORT

    def set_support(self, support_data: dict):
        conf_support = {}

        for key in support_data:
            if key == self.name:
                continue
            conf_support.update(support_data[key]['conf_objects'])

        super(Configuration, self).set_support(conf_support)

        for obj in self.conf_objects:
            obj.set_support(conf_support)

    def get_object(self, name: str, obj_type: Union[ObjectType, str]) -> ConfObject:
        cur_obj_type = obj_type
        if isinstance(obj_type, str):
            cur_obj_type = ObjectType(obj_type)

        data = list(filter(lambda obj: obj.obj_type == cur_obj_type and obj.name == name, self.conf_objects))
        try:
            return data[0]
        except IndexError:
            raise IndexError(f'Объект не найден! Имя:{name} Тип:{obj_type}')

    def to_dict(self):
        data = super(Configuration, self).to_dict()
        data.update(
             dict(
                name=self.name,
                uuid=self.uuid,
                conf_objects=[obj.to_dict() for obj in self.conf_objects]
            )
        )
        return data

    @classmethod
    def from_dict(cls, data):
        conf = cls(
            uuid=data['uuid'],
            name=data['name'],
            root_path='',
            conf_objects=list(),
        )
        conf.conf_objects = [ConfObject.from_dict(obj_data, conf) for obj_data in data['conf_objects']]
        return conf

    def __repr__(self):
        return f'<Configuration: {self.name} {self.root_path}>'


class SupportType(enum.Enum):
    NOT_EDITABLE = 0
    EDITABLE_SUPPORT_ENABLED = 1
    NOT_SUPPORTED = 2
    NONE_SUPPORT = 3


def resolve_path(obj_type: ObjectType, name: str = '') -> str:
    if obj_type == ObjectType.CONFIGURATION:
        result = f'{obj_type.value}.xml'
    elif obj_type == ObjectType.FILTER_CRITERION:
        result = f'FilterCriteria/{name}.xml'
    elif obj_type == ObjectType.CHART_OF_CHARACTERISTIC_TYPES:
        result = f'ChartsOfCharacteristicTypes/{name}.xml'
    elif obj_type == ObjectType.CHART_OF_ACCOUNTS:
        result = f'ChartsOfAccounts/{name}.xml'
    elif obj_type == ObjectType.BUSINESS_PROCESS:
        result = f'BusinessProcesses/{name}.xml'
    elif obj_type == ObjectType.CHART_OF_CALCULATION_TYPES:
        result = f'ChartsOfCalculationTypes/{name}.xml'
    else:
        result = f'{obj_type.value}s/{name}.xml'

    return result


def resolve_ext_path(obj_type: ObjectType, name: str = '') -> str:
    if obj_type == ObjectType.CONFIGURATION:
        result = ''
    elif obj_type == ObjectType.FILTER_CRITERION:
        result = f'FilterCriteria/{name}'
    elif obj_type == ObjectType.CHART_OF_CHARACTERISTIC_TYPES:
        result = f'ChartsOfCharacteristicTypes/{name}'
    elif obj_type == ObjectType.CHART_OF_ACCOUNTS:
        result = f'ChartsOfAccounts/{name}'
    elif obj_type == ObjectType.BUSINESS_PROCESS:
        result = f'BusinessProcesses/{name}'
    elif obj_type == ObjectType.CHART_OF_CALCULATION_TYPES:
        result = f'ChartsOfCalculationTypes/{name}'
    else:
        result = f'{obj_type.value}s/{name}'

    return f'{result}/Ext'

def resolve_form_path(obj_type: ObjectType, name: str = '') -> str:
    types_without_forms = [
        ObjectType.CONFIGURATION,
        ObjectType.COMMAND_GROUP,
        ObjectType.COMMON_MODULE,
        ObjectType.COMMON_ATTRIBUTE,
        ObjectType.COMMON_PICTURE,
        ObjectType.COMMON_TEMPLATE
    ]
    if obj_type in types_without_forms:
        raise ValueError(f'У объекта типа {obj_type} нет форм!')
    elif obj_type == ObjectType.CONSTANT:
        result = f'CommonForms/ФормаКонстант/Ext'
    elif obj_type == ObjectType.COMMON_FORM:
        result = f'CommonForms/{name}/Ext'
    elif obj_type == ObjectType.FILTER_CRITERION:
        result = f'FilterCriteria/Forms/{name}'
    elif obj_type == ObjectType.CHART_OF_CHARACTERISTIC_TYPES:
        result = f'ChartsOfCharacteristicTypes/Forms/{name}'
    elif obj_type == ObjectType.CHART_OF_ACCOUNTS:
        result = f'ChartsOfAccounts/Forms/{name}'
    elif obj_type == ObjectType.BUSINESS_PROCESS:
        result = f'BusinessProcesses/Forms/{name}'
    elif obj_type == ObjectType.CHART_OF_CALCULATION_TYPES:
        result = f'ChartsOfCalculationTypes/Forms/{name}'
    else:
        result = f'{obj_type.value}s/{name}/Forms'

    return f'{result}'
