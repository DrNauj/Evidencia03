import os, sys, subprocess, re

print('--- Environment check ---')
print('Python:', sys.version.splitlines()[0])
print('Executable:', sys.executable)
print('JAVA_HOME:', os.environ.get('JAVA_HOME'))
print('HADOOP_HOME:', os.environ.get('HADOOP_HOME'))
print('PYSPARK_PYTHON:', os.environ.get('PYSPARK_PYTHON'))

# java version
try:
    p = subprocess.run(['java','-version'], capture_output=True, text=True)
    out = p.stderr or p.stdout
    print('\njava -version output:')
    print(out)
    m = re.search(r'"(\d+)(?:\.|$)', out.splitlines()[0])
    if m:
        print('Detected java major version:', m.group(1))
except Exception as e:
    print('java not found or failed:', e)

# pyspark presence
try:
    import pyspark
    print('\nPySpark version:', pyspark.__version__)
except Exception as e:
    print('\nPySpark import failed:', e)

# check data file
data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'bank.csv')
print('\nData exists at', data_path, os.path.exists(data_path))
