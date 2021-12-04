# read arguments: topk, then some query words
topk="5"

q=""
for token in "$@"
do
	q+="%20"$token
done
Q=${q:3}


k=$(cat .ak)

api_link="https://youtube.googleapis.com/youtube/v3/search?maxResults="${topk}"&order=relevance&q="${Q}"&safeSearch=none&type=video&videoDefinition=standard&key="${k}


echo $api_link
echo
echo

json=$(
curl \
  ${api_link} \
  --header 'Accept: application/json' \
  --compressed
)


relative_dir="scripts/"

tmp="tmp/"
tmpfile="${relative_dir}${tmp}last_query.json"


echo $json | jq . > $tmpfile | python3 ${relative_dir}reverse_yt_json.py

# rm $tmpfile



