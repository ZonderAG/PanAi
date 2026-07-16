class ProfileStack:
    def __init__(self):
        self.profiles = []
        
    def add_packaged_frame(self, packaged):
        """
        packaged is a dict from sync_and_package.py containing:
        frame_index, profile_3d, height_mm, etc.
        """
        self.profiles.append(packaged)
        
    def get_all(self):
        return self.profiles
    
    def clear(self):
        self.profiles = []
