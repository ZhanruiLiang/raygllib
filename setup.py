from distutils.core import setup
from Cython.Build import cythonize
setup(
    name='raygllib',
    description='OpenGL utils',
    author='Ray',
    author_email='ray040123@gmail.com',
    packages=['raygllib'],
    ext_modules=cythonize('raygllib/_halfedge.pyx'),
    package_data={
        'raygllib': ['shaders/*.glsl'],
    },
)
