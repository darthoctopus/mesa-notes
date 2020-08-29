change_param() { 
    # Modifies a parameter in the current inlist. 
    # args: ($1) name of parameter 
    #       ($2) new value 
    #       ($3) filename of inlist where change should occur 
    # Additionally changes the 'inlist_0all' inlist. 
    # example command: change_param initial_mass 1.3 
    # example command: change_param log_directory 'LOGS_MS' 
    # example command: change_param do_element_diffusion .true. 
    param=$1 
    newval=$2 
    filename=$3 
    search="^\s*\!*\s*$param\s*=.+$" 
    replace="      $param = $newval" 
    sed -r -i.bak -e "s/$search/$replace/g" $filename 
    
    if [ ! "$filename" == 'inlist_0all' ]; then 
        change_param $1 $2 "inlist_0all" 
    fi 
} 

set_inlist() { 
    # Changes to a different inlist by modifying where "inlist" file points 
    # args: ($1) filename of new inlist  
    # example command: change_inlists inlist_2ms 
    newinlist=$1 
    echo "Changing to $newinlist" 
    change_param "extra_star_job_inlist2_name" "'$newinlist'" "inlist" 
    change_param "extra_controls_inlist2_name" "'$newinlist'" "inlist" 
}
