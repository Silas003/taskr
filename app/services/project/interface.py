from abc import ABC,abstractmethod


class IProjectService(ABC):

    @abstractmethod
    def create_project(self,project_data):
        pass

    @abstractmethod
    def get_project(self, project_id):
        pass
    @abstractmethod
    def get_all_projects(self,limit:int,offset:int):
        pass

    @abstractmethod
    def update_project(self, project_id, project_data):
        pass

    @abstractmethod
    def delete_project(self, project_id):
        pass

    @abstractmethod
    def get_project_by_name(self,name):
        pass

    @abstractmethod
    def get_project_by_user(self,user_id):
        pass