# Simple container to show Code Engine environment

Run this container in Code Engine to log all environmental variables declared in the Code Engine environment. Additionally it will check to see if any `CE_SERVICES` variables exist. The `CE_SERVICES` variables will only be present if you have bound a service to the Code Engine job. 

## Getting started

1. Create a Code Engine project

  ```
  ibmcloud code-engine project create
  ```

2. Create container image using the Code Engine `build` function

  ```
  ibmcloud code-engine build 
  ```

3. Create Code Engine job to run container

  ```
  ibmcloud code-engine job create 
  ```

4. Run Code Engine job and inspect output

  ```
  ibmcloud code-engine
  ```

5. 



