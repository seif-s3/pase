# Initialize Service:

1- `docker-compose up`
2- Go to `http://localhost:9090/models`. It should give you an empty list
3- Using Postman hit `http://localhost:9090/train_model_csv` with the following payload:

```
{
	"algorithm": "ARIMA",
	"dataset": "instana"
}
```

This could take time but eventually you should get this reponse
```
{
    "_id": "5b9d0eb6e21205000a8766d0",
    "acquisition_time": "2018-09-15T13:52:54.265000",
    "algorithm": "ARIMA",
    "input_end": "2018-01-29T00:00:00",
    "input_start": "2018-01-01T01:00:00",
    "input_type": "csv",
    "metadata": {
        "d": 1,
        "dataset": "instana.csv",
        "p": 2,
        "q": 0
    }
}
```

If you hit the `http://localhost:9090/models` endpoint again, you'll get the same result.

4- Activate the model by sending a post request to `http://localhost:9090/activate_model/<model_id>`

5- Make sure the model is active by going to `http://localhost:9090/active_model`

6- Generate your predictions: GET `http://localhost:9090/predict?start_time=2018-06-25T00:00:00Z&end_time=2018-06-25T06:00:00Z`. The result will look like this: 

```
{
    "_id": "5ba03164770b06004a527408",
    "end_time": "2018-06-25T06:00:00Z",
    "start_time": "2018-06-25T00:00:00Z",
    "values": [
        {
            "requests": 609.7779325447217,
            "timestamp": "2018-06-25T00:00:00Z"
        },
        {
            "requests": 609.9231336274298,
            "timestamp": "2018-06-25T01:00:00Z"
        },
        {
            "requests": 610.068334710138,
            "timestamp": "2018-06-25T02:00:00Z"
        },
        {
            "requests": 610.2135357928461,
            "timestamp": "2018-06-25T03:00:00Z"
        },
        {
            "requests": 610.3587368755542,
            "timestamp": "2018-06-25T04:00:00Z"
        },
        {
            "requests": 610.5039379582623,
            "timestamp": "2018-06-25T05:00:00Z"
        },
        {
            "requests": 610.6491390409705,
            "timestamp": "2018-06-25T06:00:00Z"
        }
    ]
}
```

7- To subscribe to changes in predictions: POST to `http://localhost:9090/subscribe`

```
{
	"url": "http://localhost:9090/healthcheck",
	"thresholds": [10, 10, 5, 2, 1, 8, 20],
	"predictions_id": "35ba0b0f6770b06006ad4d550"
}
```

`thresholds` should have the same length as the values array in the predictions. 

You'll get back a subscriber id like, and `registered: true`

```
{
    "id": "5ba0b0f6770b06006ad4d550",
    "registered": true
}
```

8- Trigger a test event: GET `http://localhost:9090/test_sub/subsriber_id`

