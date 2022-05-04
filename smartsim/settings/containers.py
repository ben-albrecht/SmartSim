class Container():
    '''Base class for container types in SmartSim.

    Container types are used to embed all the information needed to
    launch a workload within a container into a single object.
    '''

    def __init__(self, image, args='', paths=None):
        pass

class Singularity(Container):
    '''Singularity container type.'''

    def __init__(self, *args, **kwargs):
        super.__init__(*args, **kwargs)


