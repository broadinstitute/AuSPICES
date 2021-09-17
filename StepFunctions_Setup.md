How to set up the Step Function from the individual lambda functions.

## 0_setup
Configuration => Payload = Use state input at payload  
Output => :white_check_mark: ResultPath  
&ensp;&ensp;&ensp;Combine original input with result = `$.Output_0`

## Map state
Configuration => Path to items array = `$.Output_0.Payload`  
Input => :white_check_mark: Transform array items
```json
{
        "trigger.$": "$$.Map.Item.Value",
        "project_name.$": "$.project_name",
        "batch.$": "$.batch",
        "bucket.$": "$.bucket",
        "channeldict.$": "$.channeldict"
}
```
Output => ✓ ResultPath  
&ensp;&ensp;&ensp;Combine original input with result = `$.Trigger`

## 1_pe2loaddata
Configuration => Payload = Use state input at payload  
Output => :white_check_mark: ResultPath
&ensp;&ensp;&ensp;Combine original input with result = `$.Output_1`  
Parallel state  
Output => :white_check_mark: ResultPath
&ensp;&ensp;&ensp;Combine original input with result = `$.Output_2`
