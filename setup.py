from setuptools import setup, find_packages

setup(
    name="sop-generation-agent",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "strands-agents>=0.1.0",
        "boto3>=1.34.0",
        "pydantic>=2.5.0",
    ],
)
