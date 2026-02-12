#!/bin/sh

cde_user=$1
max_participants=$2
cdp_data_lake_storage=$3
demo=$4

cde_user_formatted=${cde_user//[-._]/}
d=$(date)
fmt="%-30s %s\n"

current_date=$(date +"%Y%m%d")
storage=$cdp_data_lake_storage"/"$demo"/"$current_date
echo "STORAGE: ${storage}"

echo "##########################################################"
printf "${fmt}" "CDE HOL deployment launched."
printf "${fmt}" "launch time:" "${d}"
printf "${fmt}" "performed by CDP User:" "${cde_user}"
echo "##########################################################"

echo "DELETE SETUP JOB"
cde job delete \
  --name cde125-hol-setup-job"-${demo}"

echo "CREATE FILE RESOURCE"
cde resource delete \
  --name cde125-hol-setup-fs"-${demo}"

cde resource create \
  --name cde125-hol-setup-fs"-${demo}" \
  --type files

cde resource upload \
  --name cde125-hol-setup-fs"-${demo}" \
  --local-path setup/utils.py \
  --local-path setup/setup.py

echo "CREATE PYTHON RESOURCE"
cde resource delete \
  --name datagen-hol-setup-py"-${demo}"

cde resource create \
  --type python-env \
  --name datagen-hol-setup-py"-${demo}"

cde resource upload \
  --name datagen-hol-setup-py"-${demo}" \
  --local-path setup/requirements.txt

function loading_icon_env() {
  local loading_animation=( '—' "\\" '|' '/' )

  echo "${1} "

  tput civis
  trap "tput cnorm" EXIT

  while true; do
    build_status=$(cde resource describe --name datagen-hol-setup-py"-${demo}" | jq -r '.status')
    if [[ $build_status == $"ready" ]]; then
      echo "Setup Python Env Build Completed."
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

echo "CREATE AND RUN SETUP JOB"
cde job create --name cde125-hol-setup-job"-${demo}" \
  --type spark \
  --mount-1-resource cde125-hol-setup-fs"-${demo}" \
  --application-file setup.py \
  --python-env-resource-name datagen-hol-setup-py"-${demo}" \
  --arg $max_participants \
  --arg $storage \
  --arg $demo

cde job run \
  --name cde125-hol-setup-job"-${demo}" \
  --executor-memory "8g" \
  --executor-cores 4

function loading_icon_job() {
  local loading_animation=( '—' "\\" '|' '/' )

  echo "${1} "

  tput civis
  trap "tput cnorm" EXIT

  while true; do
    job_status=$(cde run list --filter 'job[like]%cde125-hol-setup-job-${demo}' | jq -r '[last] | .[].status')
    if [[ $job_status == "succeeded" ]]; then
      echo "Setup Job Execution Completed"
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

loading_icon_job "Setup Job in Progress"

echo "##########################################################"
printf "${fmt}" "CDE ${cde_demo} HOL deployment completed."
printf "${fmt}" "completion time:" "${e}"
printf "${fmt}" "please visit CDE Job Runs UI to view in-progress demo"
echo "##########################################################"
