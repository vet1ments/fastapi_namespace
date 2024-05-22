from .resource import Resource
from typing import Sequence, ClassVar
from fastapi.params import Depends
from .utils import delete_none
from .typings import MethodHandler, MethodType, ResourceProtocol

class _Meta(type):
    global_dependencies: Sequence[Depends]
    get_dependencies: Sequence[Depends]
    post_dependencies: Sequence[Depends]
    put_dependencies: Sequence[Depends]
    delete_dependencies: Sequence[Depends]
    options_dependencies: Sequence[Depends]
    head_dependencies: Sequence[Depends]
    patch_dependencies: Sequence[Depends]
    trace_dependencies: Sequence[Depends]

    def __new__(mcs, name, bases, namespace):
        global_dependencies: Sequence[Depends] = getattr(bases[0], 'global_dependencies', None)
        if global_dependencies is not None:
            _global_dependencies = namespace.get('global_dependencies', [])
            global_dependencies = [*global_dependencies, *_global_dependencies]

        get_dependencies: Sequence[Depends] = getattr(bases[0], 'get_dependencies', None)
        if get_dependencies is not None:
            _get_dependencies = namespace.get('get_dependencies', [])
            get_dependencies = [*get_dependencies, *_get_dependencies]

        post_dependencies: Sequence[Depends] = getattr(bases[0], 'post_dependencies', None)
        if post_dependencies is not None:
            _post_dependencies = namespace.get('post_dependencies', [])
            post_dependencies = [*post_dependencies, *_post_dependencies]

        put_dependencies: Sequence[Depends] = getattr(bases[0], 'put_dependencies', None)
        if put_dependencies is not None:
            _put_dependencies = namespace.get('put_dependencies', [])
            put_dependencies = [*put_dependencies, *_put_dependencies]

        delete_dependencies: Sequence[Depends] = getattr(bases[0], 'delete_dependencies', None)
        if delete_dependencies is not None:
            _delete_dependencies = namespace.get('delete_dependencies', [])
            delete_dependencies = [*delete_dependencies, *_delete_dependencies]

        options_dependencies: Sequence[Depends] = getattr(bases[0], 'options_dependencies', None)
        if options_dependencies is not None:
            _options_dependencies = namespace.get('options_dependencies', [])
            options_dependencies = [*options_dependencies, *_options_dependencies]

        head_dependencies: Sequence[Depends] = getattr(bases[0], 'head_dependencies', None)
        if head_dependencies is not None:
            _head_dependencies = namespace.get('head_dependencies', [])
            head_dependencies = [*head_dependencies, *_head_dependencies]

        patch_dependencies: Sequence[Depends] = getattr(bases[0], 'patch_dependencies', None)
        if patch_dependencies is not None:
            _patch_dependencies = namespace.get('patch_dependencies', [])
            patch_dependencies = [*patch_dependencies, *_patch_dependencies]

        trace_dependencies: Sequence[Depends] = getattr(bases[0], 'trace_dependencies', None)
        if trace_dependencies is not None:
            _trace_dependencies = namespace.get('trace_dependencies', [])
            trace_dependencies = [*trace_dependencies, *_trace_dependencies]

        namespace.update(delete_none({
            'global_dependencies': global_dependencies,
            'get_dependencies': get_dependencies,
            'post_dependencies': post_dependencies,
            'put_dependencies': put_dependencies,
            'delete_dependencies': delete_dependencies,
            'options_dependencies': options_dependencies,
            'head_dependencies': head_dependencies,
            'patch_dependencies': patch_dependencies,
            'trace_dependencies': trace_dependencies,
        }))
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