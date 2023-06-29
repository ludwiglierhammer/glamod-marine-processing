get_id_class_pfile <- function (dck, id, pfile) {
#get_id_class <- function (dck, id) {
    patterns <- jsonlite::fromJSON(pfile)
    id_class <- rep("invalid", length(id))
    for (i in 1:length(patterns$patterns)) {
        ind <- grep(patterns$patterns[i], id)
        id_class[ind] <- names(patterns$patterns)[i]
    }
    id_class <- ifelse(dck == 849 & nchar(id) == 4, "callsign", id_class)
    id_class <- ifelse(id == "SHIP", "SHIP", id_class)
    id_class <- ifelse(id == "MASKSTID", "MASKSTID", id_class)
    id_class <- ifelse(id == "AAAA", "invalid", id_class)
    id_class <- ifelse(dck==700 & grepl("^[0-9]{5}$",id), "5digit_buoy_number", id_class)
    id_class <- ifelse(grepl("-SEQ$",id),"valid",id_class)   
    id_class <- ifelse(dck %in% c(701,730) & grepl("[A-Z]",id),"shipname",id_class)   
    id_class <- ifelse(dck==128 & grepl("^NP-[0-9]{2}$",id),"NP_station",id_class)   
    id_class <- ifelse(dck==926 & grepl("[0-9]{7}$",id),"7digit_buoy_number",id_class)   
    id_class <- ifelse(dck==116 & grepl("-[0-9]{3}$",id),"dash-shipnumber",id_class)   
    id_class <- ifelse(substr(id,3,3) == "_" & dck %in% c(705,706,707), "valid", id_class)
    id_class <- ifelse(nchar(id) == 0, "missing", id_class)
    id_class <- ifelse(id == "null", "missing", id_class)
    id_class <- ifelse(is.na(id), "missing", id_class)

    if(sum(id_class=="invalid") > 0 ) {
      cat("------- invalid ids ------\n")
      print(table(id[id_class=="invalid"]))
    }
    return(id_class)
}

