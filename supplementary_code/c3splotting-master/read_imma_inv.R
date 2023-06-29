
read_imma_inv <- function(fname) {

  config<-config::get(file = "./config_level0.yml")

  if ( !file.exists(fname) ) return(NULL)
  source("get_id_class_pfile.R")
  imma1_data <- NULL
  imma1_data <- readLines(fname)
  nrecs <- length(imma1_data)
  if(nrecs == 0 ) return(NULL)

  data<-data.frame(yr=rep(NA,times=nrecs))
  data$yr <- as.numeric(substr(imma1_data,1,4))
  max.yr<-max(data$yr)
  data$mo <- as.numeric(substr(imma1_data,5,6))
  data$dy <- as.numeric(substr(imma1_data,7,8))
  data$hr <- as.numeric(substr(imma1_data,9,12))*0.01
  if(!exists("add_date2", mode = "function")) source("inv_plot_func.R")
  data<-add_date2(data)
  names(data)<-gsub("date","report_timestamp",names(data))
  data$latitude <- as.numeric(substr(imma1_data,13,17))*0.01
  data$longitude <- as.numeric(substr(imma1_data,18,23))*0.01
  data$longitude <- ifelse(data$longitude >= 180, data$longitude-360, data$longitude)
  data$id <- trimws(substr(imma1_data,35,43))
  data$WD_observation_value <- as.numeric(substr(imma1_data,47,49))
  data$WS_observation_value <- as.numeric(substr(imma1_data,51,53))*0.1
  data$SLP_observation_value <- as.numeric(substr(imma1_data,60,64))*0.1
  data$AT_observation_value <- as.numeric(substr(imma1_data,70,73))*0.1
  data$WBT_observation_value <- as.numeric(substr(imma1_data,75,78))*0.1
  data$DPT_observation_value <- as.numeric(substr(imma1_data,80,83))*0.1
  data$RH_observation_value <- ifelse(substr(imma1_data,174,174) == "5", as.numeric(substr(imma1_data,255,257))*0.1, NA)
  if(sum(!is.na(data$RH_observation_value) > 0 ) ) cat("got relative humidity \n")
  if(sum(!is.na(data$RH_observation_value) > 0 ) ) print(range(data$RH_observation_value,na.rm=T))
  #attm5.data$rh <- as.numeric(substr(attm5,82,85))*0.1
  data$HUM_observation_value <- ifelse(!is.na(data$DPT_observation_value), 1, data$WBT_observation_value)
  data$HUM_observation_value <- ifelse(is.na(data$HUM_observation_value), data$RH_observation_value, 1)
  data$HUM_observation_value <- ifelse(!is.na(data$HUM_observation_value), 1, NA)
  data$WBT_observation_value<-NULL
  data$DPT_observation_value<-NULL
  data$RH_observation_value<-NULL
  data$SST_observation_value <- as.numeric(substr(imma1_data,86,89))*0.1
  data$dck <- substr(imma1_data,119,121)
  data$sid <- substr(imma1_data,122,124)
  data$sid <- gsub(" ","0",data$sid)
  data$pt <- as.numeric(substr(imma1_data,125,126))
  data$pt<-ifelse(is.na(data$pt),99,data$pt)

  # config files to define id types for different dck
  if ( max(data$yr,na.rm=T) <= 2014 ) {
    pfile<-paste0(config$json_files_path4,"/dck", dck.want, ".json")
  } else {
    pfile<-paste0(config$json_files_path5,"/dck", dck.want, ".json")
  }
  if ( !file.exists(pfile) ) pfile<-paste0("./json_files/dck", dck.want, ".json")
  data$id.class<-get_id_class_pfile(dck.want,data$id,pfile=pfile)
  # these need adding to the standard json files
  data$id.class<-ifelse(data$dck %in% c(700,993) & grepl("^[0-9]{5}$",data$id), "5digit_buoy_number",data$id.class)
  data$id.class<-ifelse(data$dck %in% c(926,994) & grepl("^[0-9]{7}$",data$id), "7digit_buoy_number",data$id.class)
  data$id.class<-ifelse(data$dck %in% c(994,995) & grepl("^[A-Z]{4}[0-9]{1}$",data$id), "CMAN",data$id.class)
  if ( sum(!is.na(data$report_timestamp)) > 0 ) {
    data<-calc_local(data)
    data$ltime <-as.numeric(format.POSIXct(data$local, "%H"))
    data$local<-NULL
  } else {
    data$ltime<-NA
  }
  data$yr<-NULL
  data$mo<-NULL
  data$dy<-NULL
  data$hr<-NULL
  data$date.flag<-NULL
  data$date<-NULL
  data$samp.flag<-NULL
  data$lat<-NULL
  data$lon<-NULL
  data$report_timestamp.flag<-NULL

  return(data)

}
