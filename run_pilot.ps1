& "C:\tools\apache-jmeter-5.6.3\bin\jmeter.bat" -n -t jmeter\campus_load.jmx -q jmeter\jmeter-results.properties "-Jhost=127.0.0.1" "-Jusers=1" "-Jramp=1" "-Jduration=30" "-Jjmeter.save.saveservice.output_format=csv" "-Jjmeter.save.saveservice.response_data=true" "-Jjmeter.save.saveservice.samplerData=true" -l "C:\Projects\campus-ecommerce\results\pilot\mono_1u.jtl"


