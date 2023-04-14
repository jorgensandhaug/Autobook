module.exports = async function (context, req) {
    context.log('JavaScript HTTP trigger function processed a request.');

    const body = req.body;
    if (body.type != 'payment_intent.succeeded') {
        context.res = {
            status: 200,
            body: 'Not a payment_intent.succeeded event'
        };
        return; 
    }

    context.log(body.data.object.customer);

    context.res = {
        // status: 200, /* Defaults to 200 */
        body: body
    };
}