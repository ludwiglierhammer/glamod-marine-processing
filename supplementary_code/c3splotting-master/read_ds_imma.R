
lev0<-function(dck.want,sid.want,release.want) {

    config<-config::get(file = "./config_level0.yml")

    if(!exists("read_imma_inv", mode = "function")) source("read_imma_inv.R")
    if(!exists("add_date2", mode = "function")) source("inv_plot_func.R")
    if(!exists("inv_plot", mode = "function")) source("inv_plot.R")

    patt.want<-paste0(sid.want,"-",dck.want)
    if( release.want == 4 ) {
      dir<-list.files(config$release4_path,patt=patt.want,full.names=T)
    } else {
      dir<-list.files(config$release5_path,patt=patt.want,full.names=T)
    }
    if(is.null(dir)) return()
    if(length(dir)==0) return()

    if ( !dir.exists(dir) ) return()
    flist<-list.files(dir,full.name=TRUE)
    if ( length(flist) == 0 ) return()
    if ( release.want == 5 ) flist<-flist[!grepl("2014",flist)]
    if ( release.want == 5 ) flist<-flist[!grepl("2022",flist)]
    cat(dir,"\n")
    df<-do.call(rbind,lapply(flist,read_imma_inv))

   return(df)
}
