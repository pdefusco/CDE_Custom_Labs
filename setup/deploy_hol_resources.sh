#!/bin/sh

cde_user=$1
vcluster_endpoint=$2
demo=$3

cde_user_formatted=${cde_user//[-._]/}
d=$(date)
fmt="%-30s %s\n"

echo "##########################################################"
printf "${fmt}" "CDE HOL deployment launched."
printf "${fmt}" "launch time:" "${d}"
printf "${fmt}" "performed by CDP User:" "${cde_user}"
echo "##########################################################"

echo "CREATE SPARK FILES SHARED RESOURCE"
cde resource delete --name Spark-Files-Shared \
  --vcluster-endpoint $vcluster_endpoint

cde resource create \
  --type files \
  --name Spark-Files-Shared \
  --vcluster-endpoint $vcluster_endpoint

cde resource upload \
  --name Spark-Files-Shared \
  --local-path de-pipeline-$demo/spark/parameters.conf \
  --local-path de-pipeline-$demo/spark/utils.py \
  --vcluster-endpoint $vcluster_endpoint

echo "CREATE PYTHON ENVIRONMENT SHARED RESOURCE"
cde resource delete \
  --name Python-Env-Shared \
  --vcluster-endpoint $vcluster_endpoint

cde resource create \
  --type python-env \
  --name Python-Env-Shared \
  --vcluster-endpoint $vcluster_endpoint

cde resource upload \
  --name Python-Env-Shared \
  --local-path de-pipeline-$demo/spark/requirements.txt \
  --vcluster-endpoint $vcluster_endpoint

function loading_icon_env() {
  local loading_animation=( '—' "\\" '|' '/' )

  echo "${1} "

  tput civis
  trap "tput cnorm" EXIT

  while true; do
    build_status=$(cde resource describe --name Python-Env-Shared --vcluster-endpoint $vcluster_endpoint | jq -r '.status')
    if [[ $build_status == $"ready" ]]; then
      echo "Python Env Build Has Completed"
      break
    else
      for frame in "${loading_animation[@]}" ; do
        printf "%s\b" "${frame}"
        sleep 1
      done
    fi
  done
  printf " \b\n"
}

loading_icon_env "Python Env Build in Progress"

e=$(date)

echo "##########################################################"
printf "${fmt}" "CDE ${cde_demo} HOL deployment completed."
printf "${fmt}" "completion time:" "${e}"
printf "${fmt}" "please visit CDE Resources UI to validate resources."
echo "##########################################################"
