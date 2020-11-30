from pathlib import Path
from abc import ABC, abstractmethod

from mdclasses.configuration_enums import Format, ObjectType


class ABCPathResolver(ABC):

    def __init__(self, file_format: Format):
        self.file_format = file_format

    @abstractmethod
    def conf_file_path(self, obj_type: ObjectType, name: str = '') -> Path:
        pass

    @abstractmethod
    def ext_path(self, obj_type: ObjectType, name: str = '') -> Path:
        pass

    @abstractmethod
    def form_path(self, obj_type: ObjectType, obj_name: str = '', form_name: str = '') -> Path:
        pass

    @abstractmethod
    def type_path(self, obj_type: ObjectType) -> Path:
        pass


def get_path_resolver(file_format: Format) -> ABCPathResolver:
    if file_format == Format.EDT:
        return EDTPathResolver(file_format)
    elif file_format == Format.CONFIGURATOR:
        return XMLPathResolver(file_format)
    else:
        raise NotImplementedError(f'Не определена обработка формата {file_format}')


class EDTPathResolver(ABCPathResolver):

    def conf_file_path(self, obj_type: ObjectType, name: str = '') -> Path:
        raise NotImplementedError(f'Не определена обработка формата {self.file_format}')

    def ext_path(self, obj_type: ObjectType, name: str = '') -> Path:
        raise NotImplementedError(f'Не определена обработка формата {self.file_format}')

    def form_path(self, obj_type: ObjectType, obj_name: str = '', form_name: str = '') -> Path:
        raise NotImplementedError(f'Не определена обработка формата {self.file_format}')

    def type_path(self, obj_type: ObjectType) -> Path:
        raise NotImplementedError(f'Не определена обработка формата {self.file_format}')


class XMLPathResolver(ABCPathResolver):

    def conf_file_path(self, obj_type: ObjectType, name: str = '') -> Path:
        if obj_type == ObjectType.CONFIGURATION:
            result = f'{obj_type.value}.xml'
        else:
            result = f'{self.type_path(obj_type)}/{name}.xml'

        return Path(result)

    def ext_path(self, obj_type: ObjectType, name: str = '') -> Path:
        if obj_type == ObjectType.CONFIGURATION:
            result = Path('')
        else:
            result = Path(f'{self.type_path(obj_type)}/{name}')

        return Path(f'{result}/Ext')

    def form_path(self, obj_type: ObjectType, obj_name: str = '', form_name: str = '') -> Path:
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
            result = f'CommonForms/ФормаКонстант/'
        elif obj_type == ObjectType.COMMON_FORM:
            result = f'CommonForms/{obj_name}/'
        else:
            result = f'{self.type_path(obj_type)}/{obj_name}/Forms/{form_name}'

        return Path(f'{result}')

    def type_path(self, obj_type: ObjectType) -> Path:
        if obj_type == ObjectType.CONFIGURATION:
            result = Path('')
        elif obj_type == ObjectType.FILTER_CRITERION:
            result = Path(f'FilterCriteria')
        elif obj_type == ObjectType.CHART_OF_CHARACTERISTIC_TYPES:
            result = Path(f'ChartsOfCharacteristicTypes')
        elif obj_type == ObjectType.CHART_OF_ACCOUNTS:
            result = Path(f'ChartsOfAccounts')
        elif obj_type == ObjectType.BUSINESS_PROCESS:
            result = Path(f'BusinessProcesses')
        elif obj_type == ObjectType.CHART_OF_CALCULATION_TYPES:
            result = Path(f'ChartsOfCalculationTypes')
        else:
            result = Path(f'{obj_type.value}s')

        return Path(result)
