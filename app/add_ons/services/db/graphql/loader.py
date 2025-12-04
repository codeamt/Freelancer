# app/add_ons/services/graphql/loader.py
from dataloader import DataLoader
from add_ons.services import get_service

class DataLoaderRegistry:
    def __init__(self):
        self._loaders = {}
        
    def register(self, name: str, batch_fn):
        self._loaders[name] = DataLoader(batch_fn)
        
    def __getattr__(self, name):
        if name not in self._loaders:
            service = get_service(name.split('_')[0])
            self.register(name, service.batch_get)
        return self._loaders[name]