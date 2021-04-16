import os
import subprocess
import requests
import json
import sys
import pandas as pd

import ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context





#from tcga downloader import *
#ids=process_manifests(manifest_file)

'''
Match tumor and normal samples to a patient through GDC API. This will provide metadata that
for associated files including sample type(tumor /normal) patient ID(TCGA barcode), etc

The general query structure will look like this:

curl "https://gdc-api.nci.nih.gov/files?size=100000&format=tsv&filters=XXXX&fields=YYYY"

filters= :

The XXXX will be replaced with a URL-encoded JSON query that will filter a list of files. The JSON query can be generated yourself and then URL encoded, or the filtering can be performed on the GDC Data Portal (https://gdc-portal.nci.nih.gov/search/s?facetTab=files). You can copy and paste the string that appears where the * are displayed in the following:

https://gdc-portal.nci.nih.gov/search/f?filters=**********&facetTab=cases

'''

def prepare_payload(ids,data_type=None):

    #"Gene Expression Quantification"
    
    "Workflow Type" "HTSeq-Counts"

    "Data Category" "transcriptome profilling"
    "Experimental Strategy" "RNA-Seq"

    no_of_samples=len(ids)
    part1='''{
    "filters":{
        "op":"and",
        "content":[
            {
                "op":"in",
                "content":{
                    "field":"files.file_id",
                    "value":[%s]
                }
            },
            {
                "op":"=",
                "content":{
                    "field":"files.data_type",
                    "value":"%s"
                }
            }
        ]
    },'''%(",\n".join(ids),data_type)


    part2=''' "format":"TSV","fields":"file_id,file_name,cases.submitter_id,cases.disease_type,cases.case_id,data_category,data_type,cases.samples.tumor_descriptor,cases.samples.tissue_type,cases.samples.sample_type,cases.samples.submitter_id,cases.samples.sample_id,cases.samples.portions.analytes.aliquots.aliquot_id,cases.samples.portions.analytes.aliquots.submitter_id","size":"%d"}'''%no_of_samples

    payload_command='%s %s'%(part1,part2)

    payloadfile='payloadv3.txt'
    with open(payloadfile,'w') as output_:
        output_.write(payload_command)
    return payloadfile


def get_ids(manifest):
    try:
#manifest='all.txt'
        with open (manifest,'r') as input_:
            ids=["\"%s\""%i.strip('\n').split('\t')[0] for i in input_][1:]

        no_of_samples=len(ids)
        return ids
    except Exception as ex:
        return None
    #print(ids)


def get_metadata(payloadfile):
    metadata='Metadata.tsv'
    webaddr='\'https://api.gdc.cancer.gov/files\''
    args=['curl', '--request POST', '--header','\"Content-Type: application/json\"',
      '--data','@%s'%payloadfile,webaddr, '>', metadata]

    single=' '.join(args)
    print(single)
    os.system(single)
    return metadata


#def get_metadatada():
 #   ids=process_manifest()
  #  if ids==None:
   #     print('Error encountered\nPlease ensure that you are using the correct manifest file')
   # else:
   #     payloadfile=prepare_payload(ids)
   #     download_data(payloadfile)

def download_data(metadatafile,sep='\t',outdir='downloads'):
    df=pd.DataFrame()
    data_df=pd.read_csv(metadatafile,sep=sep)
    sampletypes=data_df['cases.0.samples.0.sample_type'].unique()
    sampletypes=sampletypes.tolist()
    curr_dir=os.getcwd()
    
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    else:
        print('output directory exists\ndata may be overwritten')
        
    for sampletype in sampletypes:
        sel=data_df[data_df['cases.0.samples.0.sample_type'].str.contains(sampletype)][['file_id',
                                                                               'file_name']]

        sampledir="%s/%s"%(outdir,sampletype)
        
        if not os.path.exists(sampledir):
            os.mkdir(sampledir)
        else:
            print('sample type directory exists\ndata may be overwritten')
            
        
        os.chdir(sampledir)
        all_file_ids=sel['file_id'].values
        download_list=[]
        for file_id in all_file_ids:
            args=['curl', '--remote-name', '--remote-header-name',
                  '\'https://api.gdc.cancer.gov/data/%s\''%file_id]
            cmd=' '.join(args)
            print('downloading %s'%file_id)
            os.system(cmd)
            #download_list.append(' '.join(args))
        os.chdir(curr_dir)
    print('Download complete\nAll data has been downloaded to ------------->%s'%outdir)
        
        
    
