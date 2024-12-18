find src/RAG -type f -name '*.py' -mmin -620
find src/RAG -type f -name '*.py' -mmin -620 | xargs echo /add
find src/RAG -type f -name '*.py' -mmin -720 | sed 's/^/\/add /'
