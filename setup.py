from setuptools import setup
readme = open("README.md","r").read()

setup(
    name = 'botanalytics',
    version = '0.2.6',
    description = 'Conversational analytics & engagement tool for chatbots',
    long_description = readme,
    long_description_content_type='text/markdown',
    url = 'https://github.com/Botanalyticsco/botanalytics-python',
    author = 'Enis Gayretli',
    author_email = 'tech@botanalytics.co',
    license = 'MIT',
    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ],
    keywords = 'botanalytics bot bots analytics chatbot chatbots conversational facebook google amazon ibm voice actions lex alexa messsenger assistant watson',
    install_requires = [
        'requests',
        'futures; python_version == "2.7"'
    ],
    packages = ['botanalytics']
)
