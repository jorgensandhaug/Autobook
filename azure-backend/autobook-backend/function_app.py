import azure.functions as func
import logging

app = func.FunctionApp()
logging.basicConfig(level=logging.INFO)


@app.function_name(name="webhook")
@app.route(route="webhook") 
def webhook(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    logging.info(req.get_body())
    return func.HttpResponse("HttpTrigger1 function processed a request!!!")


@app.function_name(name="test")
@app.route(route="test") 
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    logging.info(req.get_body())
    return func.HttpResponse("HttpTrigger1 function processed a request!!!")


@app.function_name(name="HttpTrigger1")
@app.route(route="req")
def main(req):
    user = req.params.get('user')
    return f'Hello, {user}!'

@app.function_name(name="episode-poller")
@app.schedule(schedule="0 0 11 * * *",
              arg_name="mytimer",
              run_on_startup=True) 
def test_function(mytimer: func.TimerRequest) -> None:
    logging.info('Python timer trigger function ran at %s', mytimer.past_due)