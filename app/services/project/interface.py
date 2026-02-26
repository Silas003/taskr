from abc import ABC,abstractmethod

from app.models.Project import Project


class IProjectService(ABC):

    @abstractmethod
    def create_project(self,project_data)->Project:
        pass

    @abstractmethod
    def get_project(self, project_id:int):
        pass
    @abstractmethod
    def get_all_projects(self,limit:int,offset:int):
        pass

    @abstractmethod
    def update_project(self, project_id:int, project_data):
        pass

    @abstractmethod
    def delete_project(self, project_id:int):
        pass

    @abstractmethod
    def get_project_by_name(self,name:str):
        pass

    @abstractmethod
    def get_project_by_user(self,user_id:int):
        pass

    @abstractmethod
    def get_project_members(self,project_id:int,user_id:int):
        pass