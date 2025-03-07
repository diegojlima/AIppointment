import setuptools

with open("README.md") as fp:
    long_description = fp.read()

setuptools.setup(
    name="aippointment_cdk",
    version="0.1.0",
    description="CDK app for AIppointment",
    author="AIppointment Team",
    package_dir={"": "."},
    packages=setuptools.find_packages(),
    install_requires=[
        "aws-cdk-lib==2.103.0",
        "constructs>=10.0.0",
        "jsii>=1.84.0",
        "boto3>=1.28.0",
        "pytest>=7.0.0",
    ],
    python_requires=">=3.8",
)
