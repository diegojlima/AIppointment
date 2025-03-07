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
        "aws-cdk-lib==2.114.1",
        "constructs==10.3.0",
        "jsii==1.92.0",
        "boto3==1.29.3",
        "pytest==7.4.3",
    ],
    python_requires=">=3.8",
)
