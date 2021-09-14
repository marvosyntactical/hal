# read arguments: topk, then some query words
topk=$1

q=""
for token in "${@:2}"
do
	q+= "%20"+$token
done
q=${q:3}


API_KEY="AIzaSyAdH_CHyRRxBxMYGa7lnhJxtyqL5LqFkm8"

api_link='https://youtube.googleapis.com/youtube/v3/search?maxResults=${topk}&order=relevance&q=${q}&safeSearch=none&type=video&videoDefinition=standard&key='+${API_KEY}

echo $api_link
echo
echo

json=$(
curl \
  ${api_link} \
  --header 'Accept: application/json' \
  --compressed
)


tmp="tmp/"
tmpfile="${tmp}last_query.json"

echo $json | jq . > $tmpfile | python3 reverse_yt_json.py

rm $tmpfile



