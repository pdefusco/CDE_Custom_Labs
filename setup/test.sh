function loading_icon() {
  local loading_animation=( '—' "\\" '|' '/' )

  echo "${1} "

  tput civis
  trap "tput cnorm" EXIT

  while true; do
    job_status=$(cde run list --filter 'job[like]%mkt-hol-setup-pauldefusco%' | jq -r '.[].status')
    if [[ $job_status == $"succeeded" ]]; then
      echo "job has completed"
    else
      for frame in "${loading_animation[@]}" ; do
        printf "%s\b" "${frame}"
        sleep 1
      done
    fi
  done
  printf " \b\n"
}

loading_icon "Table Setup in Progress"
