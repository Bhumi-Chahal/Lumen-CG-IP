"""Silent event interface until Level 1 procedural audio is imported."""
class AudioManager:
    def play(self,*args,**kwargs):pass
    def update(self,*args,**kwargs):pass
    def __getattr__(self,name):return lambda *args,**kwargs: None
audio=AudioManager()
