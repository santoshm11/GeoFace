#!/usr/bin/env bash
# Use this script to test if a given TCP host/port are available

WAITFORIT_cmdname=${0##*/}

echoerr() { if [[ $WAITFORIT_QUIET -ne 1 ]]; then echo "$@" 1>&2; fi }

usage()
{
    cat << USAGE >&2
Usage:
    $WAITFORIT_cmdname host:port [-s] [-t timeout] [-- command args]
    -h HOST | --host=HOST       Host or IP under test
    -p PORT | --port=PORT       TCP port under test
                                Alternatively, you specify the host and port as host:port
    -s | --strict               Only execute subcommand if the test succeeds
    -q | --quiet                Don't output any status messages
    -t TIMEOUT | --timeout=TIMEOUT
                                Timeout in seconds, zero for no timeout
    -- COMMAND ARGS             Execute command with args after the test finishes
USAGE
    exit 1
}

WAITFORIT_HOST=
WAITFORIT_PORT=
WAITFORIT_TIMEOUT=15
WAITFORIT_STRICT=0
WAITFORIT_QUIET=0

# Parse arguments
while [[ $# -gt 0 ]]
do
    case "$1" in
        *:* )
        WAITFORIT_hostport=(${1//:/ })
        WAITFORIT_HOST=${WAITFORIT_hostport[0]}
        WAITFORIT_PORT=${WAITFORIT_hostport[1]}
        shift 1
        ;;
        --child)
        WAITFORIT_CHILD=1
        shift 1
        ;;
        -q | --quiet)
        WAITFORIT_QUIET=1
        shift 1
        ;;
        -s | --strict)
        WAITFORIT_STRICT=1
        shift 1
        ;;
        -h)
        WAITFORIT_HOST="$2"
        if [[ $WAITFORIT_HOST == "" ]]; then break; fi
        shift 2
        ;;
        --host=*)
        WAITFORIT_HOST="${1#*=}"
        shift 1
        ;;
        -p)
        WAITFORIT_PORT="$2"
        if [[ $WAITFORIT_PORT == "" ]]; then break; fi
        shift 2
        ;;
        --port=*)
        WAITFORIT_PORT="${1#*=}"
        shift 1
        ;;
        -t)
        WAITFORIT_TIMEOUT="$2"
        if [[ $WAITFORIT_TIMEOUT == "" ]]; then break; fi
        shift 2
        ;;
        --timeout=*)
        WAITFORIT_TIMEOUT="${1#*=}"
        shift 1
        ;;
        --)
        shift
        WAITFORIT_CLI=("$@")
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [[ "$WAITFORIT_HOST" == "" || "$WAITFORIT_PORT" == "" ]]; then
    echoerr "Error: you need to provide a host and port to test."
    usage
fi

WAITFORIT_TIMEOUT=${WAITFORIT_TIMEOUT:-15}
WAITFORIT_STRICT=${WAITFORIT_STRICT:-0}
WAITFORIT_CHILD=${WAITFORIT_CHILD:-0}
WAITFORIT_QUIET=${WAITFORIT_QUIET:-0}

# check to see if timeout is from busybox?
WAITFORIT_TIMEOUT_PATH=$(type -p timeout)
WAITFORIT_TIMEOUT_PATH=$(realpath $WAITFORIT_TIMEOUT_PATH 2>/dev/null || readlink -f $WAITFORIT_TIMEOUT_PATH)

WAITFORIT_BUSYTIMEOUT=0
if [[ "$WAITFORIT_TIMEOUT_PATH" =~ "busybox" ]]; then
    WAITFORIT_BUSYTIMEOUT=1
fi

if ! type -p nc >/dev/null; then
    echoerr "nc (netcat) is not available. Install it (e.g., apt-get install netcat)."
    exit 1
fi

if [[ $WAITFORIT_CHILD -gt 0 ]]; then
    # execute the child command
    exec "${WAITFORIT_CLI[@]}"
else
    # main wait loop
    WAITFORIT_start_ts=$(date +%s)
    while :
    do
        if nc -z "$WAITFORIT_HOST" "$WAITFORIT_PORT" >/dev/null 2>&1; then
            break
        fi
        WAITFORIT_now_ts=$(date +%s)
        if [[ $WAITFORIT_TIMEOUT -gt 0 ]]; then
            if [[ $((WAITFORIT_now_ts - WAITFORIT_start_ts)) -ge $WAITFORIT_TIMEOUT ]]; then
                echoerr "Timeout occurred after waiting $WAITFORIT_TIMEOUT seconds for $WAITFORIT_HOST:$WAITFORIT_PORT."
                if [[ $WAITFORIT_STRICT -eq 1 ]]; then
                    exit 1
                fi
                break
            fi
        fi
        sleep 1
    done
    if [[ $WAITFORIT_STRICT -eq 1 && $? -ne 0 ]]; then
        exit 1
    fi
    exec "${WAITFORIT_CLI[@]}"
fi