from setuptools import setup
readme = open("README.md","r").read()

setup(
    name = 'botanalytics',
    version = '0.0.1',
    description = 'Conversational analytics & engagement tool for chatbots',
    long_description = readme,
    url = 'https://github.com/Botanalyticsco/botanalytics-python',
    author = 'Beyhan Esen',
    author_email = 'beyhan@botanalytics.co',
    license = 'MIT',
    classifiers = [
        'Intended Auidience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.x'
    ],
    keywords = 'botanalytics bot bots analytics chatbot chatbots conversational facebook google amazon ibm voice actions lex alexa messsenger assistant watson',
    instal_requires = ['requests'],
    packages = ['botanalytics']
)
