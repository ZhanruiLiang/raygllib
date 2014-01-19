from distutils.core import setup
setup(
    name='raygllib',
    description='OpenGL utils',
    author='Ray',
    author_email='ray040123@gmail.com',
    packages=['raygllib', 'raygllib.objreader'],
    package_data={
        'raygllib.objreader': ['*.glsl']
    },
)
