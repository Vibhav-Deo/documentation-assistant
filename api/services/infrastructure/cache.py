class SimpleCache:
    def __init__(self):
        self.cache = {}
    
    def get(self, key): 
        return self.cache.get(key)
    
    def set(self, key, value): 
        self.cache[key] = value
    
    def clear(self): 
        self.cache.clear()
    
    def get_stats(self): 
        return {"cache_size": len(self.cache)}