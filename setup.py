from distutils.core import setup
from Cython.Build import cythonize
setup(
    name='raygllib',
    description='OpenGL utils',
    author='Ray',
    author_email='ray040123@gmail.com',
    packages=['raygllib', 'raygllib.ui'],
    ext_modules=cythonize(['raygllib/_model.pyx', 'raygllib/ui/_render.pyx']),
    package_data={
        'raygllib': ['shaders/*.glsl', 'models/*'],
        'raygllib.ui': ['shaders/*.glsl', 'textures/*']
    },
)
