# FastDebug
A FastAPI based python debugger

This is a **very** basic debugger that runs inside of a FastAPI server. 

**NOTE:** This server is only semi-functional. It currently pauses on every line whether there is a break point or not.  It also doesn't handle exceptions in the target script very well. 


### Why in the heck would you build this?
It's a proof of concept for a debugger that an LLM could use to debug a python script. LLMs can use OpenAPI compliant APIs easily via LangChain OpenAPI function chains! 


## Usage

![image](https://github.com/kreneskyp/fastdebug/assets/68635/179902cd-a24e-4387-b5d1-0e8e48045912)


1. Start the server

    ```
    poetry run server
    ```

2. Init the session

    Init the debugging with a `POST` to `/debug/init`
The payload should be a classpath, where the last element is the entry function. For example, to start `start()` in `foo.py` send this payload

    ```
    {classpath: "foo.start"}
    ```

3. Start the script

    Start the debugging run with a `POST` to `/debug/start`

4. List variables from paused frame

    Fetch variables from the current frame with a `GET` to `/debug/vars`


5. Step to the next line

    Step to the next line with a `POST` to `/debug/step`
