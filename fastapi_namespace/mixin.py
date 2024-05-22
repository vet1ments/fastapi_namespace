from .resource import Resource
from typing import Sequence
from fastapi.params import Depends

class _Meta(type):
    def __new__(mcs, name, bases, namespace):
        global_dependencies: Sequence[Depends] = getattr(bases[0], 'global_dependencies', [])
        global_dependencies = [*global_dependencies, namespace.get('global_dependencies', [])]
        get_dependencies: Sequence[Depends] = getattr(bases[0], 'get_dependencies', [])
        get_dependencies = [*get_dependencies, namespace.get('get_dependencies', [])]
        post_dependencies: Sequence[Depends] = getattr(bases[0], 'post_dependencies', [])
        post_dependencies = [*post_dependencies, namespace.get('post_dependencies', [])]
        put_dependencies: Sequence[Depends] = getattr(bases[0], 'put_dependencies', [])
        put_dependencies = [*put_dependencies, namespace.get('put_dependencies', [])]
        delete_dependencies: Sequence[Depends] = getattr(bases[0], 'delete_dependencies', [])
        delete_dependencies = [*delete_dependencies, namespace.get('delete_dependencies', [])]
        options_dependencies: Sequence[Depends] = getattr(bases[0], 'options_dependencies', [])
        options_dependencies = [*options_dependencies, namespace.get('options_dependencies', [])]
        head_dependencies: Sequence[Depends] = getattr(bases[0], 'head_dependencies', [])
        head_dependencies = [*head_dependencies, namespace.get('head_dependencies', [])]
        patch_dependencies: Sequence[Depends] = getattr(bases[0], 'patch_dependencies', [])
        patch_dependencies = [*patch_dependencies, namespace.get('patch_dependencies', [])]
        trace_dependencies: Sequence[Depends] = getattr(bases[0], 'trace_dependencies', [])
        trace_dependencies = [*trace_dependencies, namespace.get('trace_dependencies', [])]

        namespace.update({
            'global_dependencies': global_dependencies,
            'get_dependencies': get_dependencies,
            'post_dependencies': post_dependencies,
            'put_dependencies': put_dependencies,
            'delete_dependencies': delete_dependencies,
            'options_dependencies': options_dependencies,
            'head_dependencies': head_dependencies,
            'patch_dependencies': patch_dependencies,
            'trace_dependencies': trace_dependencies,
        })
        return type.__new__(mcs, name, bases, namespace)

class MixinBase(Resource, metaclass=_Meta):
    global_dependencies: Sequence[Depends]
    get_dependencies: Sequence[Depends]
    post_dependencies: Sequence[Depends]
    put_dependencies: Sequence[Depends]
    delete_dependencies: Sequence[Depends]
    options_dependencies: Sequence[Depends]
    head_dependencies: Sequence[Depends]
    patch_dependencies: Sequence[Depends]
    trace_dependencies: Sequence[Depends]