# RAG LLM Performance Comparison

## Objective

This document outlines the performance and accuracy of 11 different Large Language Models for our insurance document analysis task. The goal was to identify the model that provides the best balance of speed, accuracy, and reliability.

---

## Questions

Remember this questions stay same throughout the testing process.

```json
{
  "documents": "https://hackrx.blob.core.windows.net/assets/UNI%20GROUP%20HEALTH%20INSURANCE%20POLICY%20-%20UIIHLGP26043V022526%201.pdf?sv=2023-01-03&spr=https&st=2025-07-31T17%3A06%3A03Z&se=2026-08-01T17%3A06%3A00Z&sr=b&sp=r&sig=wLlooaThgRx91i2z4WaeggT0qnuUUEzIUKj42GsvMfg%3D",
  "questions": [
    "What is the waiting period for Pre-Existing Diseases (PED) under this policy?",
    "Are expenses for cosmetic or plastic surgery covered?",
    "AWhat is the maximum number of days for which Post-hospitalisation Medical Expenses are covered?",
    "What are the room rent limits specified in the "Other Special Conditions"?",
    "According to the policy, what is the definition of a "Hospital"?",
    "Are the costs for an organ donor's screening and pre-hospitalization covered?",
    "Is treatment received outside of India covered under this policy?",
    "What is the toll-free number for the TPA, VIDAL HEALTH?",
    "Does this policy cover expenses related to participation in hazardous or adventure sports?",
    "A policyholder is treated for arthritis via Domiciliary Hospitalisation for 4 days because a hospital bed was unavailable. Are the expenses for the first day of treatment covered?",
    "A 20-year-old dependent child, who is unmarried and unemployed, needs dental surgery due to an accident. Is pre-authorization required for their claim?",
    "If a policyholder undergoes a covered surgery and the hospital bill includes a charge for a "walker" and a "cervical collar," which of these two items is payable?",
    "A claim is submitted with a prescription from a registered Medical Practitioner who is a family member of the insured. Are the costs for the prescribed medicines reimbursable?",
    "If a policyholder's claim is rejected and they do not file a lawsuit within 12 months, what is the status of the claim?",
    "A newly-wedded spouse is added to an employer-employee group policy mid-term. If this new member needs a knee replacement for a pre-existing condition three months after joining, how will the policy's clauses on "Addition of a Member," "Waiting Periods," and "Portability" interact to determine if the claim is payable?"
  ]
}
```

---

## Answers

```text
1. What is the waiting period for Pre-Existing Diseases (PED) under this policy?
The waiting period for Pre-Existing Diseases has been waived for this specific group policy.

2. Are expenses for cosmetic or plastic surgery covered?
No, expenses for cosmetic or plastic surgery are not covered, unless they are required for reconstruction following an accident, burns, or cancer, and are certified as medically necessary.

3. What is the maximum number of days for which Post-hospitalisation Medical Expenses are covered?
Post-hospitalisation medical expenses are covered for up to 60 days from the date of discharge.

4. What are the room rent limits specified in the "Other Special Conditions"?
For a normal room, the rent is limited to 2% of the Sum Insured (SI), and for an ICU, the limit is 4% of the SI, inclusive of nursing charges.

5. According to the policy, what is the definition of a "Hospital"?
A hospital is an institution registered with local authorities that has at least 10 in-patient beds in towns with a population under 1 million (or 15 beds elsewhere), qualified nursing staff and medical practitioners on duty 24/7, a fully equipped operation theatre, and maintains daily patient records.

6. Are the costs for an organ donor's screening and pre-hospitalization covered?
No, the policy explicitly excludes pre-hospitalization expenses, screening expenses, and costs associated with the acquisition of the donor's organ.

7. What is the time limit for submitting reimbursement claims for post-hospitalization expenses?
Claims for post-hospitalization expenses must be submitted within 15 days from the completion of the treatment.

8. Is treatment received outside of India covered under this policy?
No, treatment received outside of India is a standard permanent exclusion under this policy.

9. What is the toll-free number for the TPA, VIDAL HEALTH?
The toll-free numbers for VIDAL HEALTH TPA are 1860-425-0251 and 080-4626-7018.

10. Does this policy cover expenses related to participation in hazardous or adventure sports?
No, expenses for any treatment needed due to participation as a professional in hazardous or adventure sports are excluded

11. A policyholder is treated for arthritis via Domiciliary Hospitalisation for 4 days because a hospital bed was unavailable. Are the expenses for the first day of treatment covered?
No, the expenses would not be covered. While Domiciliary Hospitalisation is a benefit, the policy explicitly lists arthritis, gout, and rheumatism as conditions for which this benefit is not payable.

12. A 20-year-old dependent child, who is unmarried and unemployed, needs dental surgery due to an accident. Is pre-authorization required for their claim?
No, pre-authorization is not required. The policy specifies that pre-authorization is only mandatory for Orthodontic Treatment claims for dependent children below 18 years. Since the child is 20 and the surgery is due to an accident (not orthodontics), this specific pre-authorization rule does not apply.

13. If a policyholder undergoes a covered surgery and the hospital bill includes a charge for a "walker" and a "cervical collar," which of these two items is payable?
Neither item is payable. The annexure of non-medical expenses explicitly states that "WALKING AIDS CHARGES" are "Not Payable" and "CERVICAL COLLAR" is "Not Payable".

14. A claim is submitted with a prescription from a registered Medical Practitioner who is a family member of the insured. Are the costs for the prescribed medicines reimbursable?
No, the costs are not reimbursable. The policy excludes expenses for certification, diagnosis, or treatment by a family member.

15. If a policyholder's claim is rejected and they do not file a lawsuit within 12 months, what is the status of the claim?
The claim is considered abandoned. The policy states that if a rejected claim is not made the subject of a suit in a court of law within 12 calendar months, the claim is deemed abandoned and is not recoverable thereafter.

16. A newly-wedded spouse is added to an employer-employee group policy mid-term. If this new member needs a knee replacement for a pre-existing condition three months after joining, how will the policy's clauses on "Addition of a Member," "Waiting Periods," and "Portability" interact to determine if the claim is payable?
The claim would be payable. The "Other Special Conditions" for this specific group policy explicitly state that the Pre-Existing Disease Waiting Period is waived. Therefore, even though knee replacement for non-accidental causes typically has a waiting period, this waiver for the group overrides that exclusion, making the new member eligible for the claim from day one of their cover.
```

---

## Results

### Model :- meta/llama3-8b-instruct

Model Time :- 10.57s

Model answers -

```json

{
    "answers": [
        "The waiting period for Pre-Existing Diseases (PED) under this policy is the number of months as mentioned in the Policy schedule or Certificate of Insurance, of continuous coverage after the date of inception of the first policy with us, which is then waived off in this specific policy as per the Other Special Condition Details.",
        "Expenses for cosmetic or plastic surgery are excluded from coverage unless required for reconstruction following an accident, burns, or cancer or as part of medically necessary treatment to remove a direct and immediate health risk to the insured, and certified by the attending medical practitioner.",
        "The maximum number of days for which Post-hospitalisation Medical Expenses are covered is 60 days, as per the document.",
        "According to the \"Other Special Conditions\", the room rent limits specified are 2% of the sum insured for normal category and 4% of the sum insured for ICU.",
        "A hospital is defined as any institution established for in-patient care and day care treatment of illness and/or injuries, and which has been registered as a hospital with the local authorities under the Clinical Establishments (Registration and Regulation) Act 2010 or under enactments specified under the Schedule of Section 56(1) and the said act, or complies with all minimum criteria as under.",
        "The information is not available in the provided documents.",
        "Treatment received outside India is not covered under this policy as per exclusion 20.",
        "The toll-free number for the TPA, VIDAL HEALTH TPA PRIVATE LTD, is 1800-42025-251/080-46267018.",
        "Expenses related to treatment necessitated due to participation as a professional in hazardous or adventure sports, such as para-jumping, rock climbing, or scuba diving, are specifically excluded under Code-Excl09.",
        "The expenses for the first day of treatment are not covered under Domiciliary Hospitalisation, as Domiciliary Hospitalisation requires the treatment to continue for at least 3 consecutive days.",
        "In respect of Orthodontic Treatment claims for Dependent Children below 18 years, pre-authorisation is a must; however, since the child is 20 years old and not below 18, no pre-authorisation is required for their claim.",
        "According to Annexure-I, \"BELTS/ BRACES\" are payable for cases who have undergone surgery of thoracic or lumbar spine, while \"CERVICAL COLLAR\" is listed as Not Payable under section 43.",
        "According to clause 18, certification/diagnosis/treatment by a family member or a person who stays with the insured person is not eligible for reimbursement, except for proven material costs which are eligible for reimbursement as per the applicable cover.",
        "If a claim is rejected or partially settled and is not the subject of any pending suit or other proceeding, as the case may be, within twelve months from the date of such rejection or settlement, the claim shall be deemed to have been abandoned and Our liability shall be extinguished and shall not be recoverable thereafter.",
        "The claim for the knee replacement surgery will be excluded until the end of the waiting period specified for the pre-existing disease in the Policy schedule or Certificate of Insurance, which is longer than the waiting period for newly added members. This is because the knee replacement surgery is for a pre-existing condition, falling under the exclusion for expenses related to the treatment of a pre-existing disease until the expiry of the number of months, as mentioned in the Policy schedule or Certificate of Insurance, of continuous coverage."
    ]
}
```

### Model :- mistralai/mistral-nemo-12b-instruct

Model Time :- 9.50s

Model answers -

```json

{
    "answers": [
        "The Pre-Existing Disease Waiting Period is waived off for policy number 1106002825P104574949.",
        "Cosmetic or plastic surgery expenses are generally not covered unless they're for reconstructive purposes following an accident, burns, or cancer, or for removing an immediate health risk, with a medical practitioner's certification.",
        "Post-hospitalisation Medical Expenses are covered for up to 60 days.",
        "Room rent limit is 2% of Sum Insured for Normal and 4% of Sum Insured for ICU (inclusive of nursing charges).",
        "A \"Hospital\" is any institution registered with local authorities providing in-patient and day care treatment, adhering to specified criteria.",
        "The information is not available in the provided documents.",
        "No, treatment received outside India is not covered under this policy as per clause 20.",
        "The toll-free number for VIDAL HEALTH TPA is 18604250251/08046267018.",
        "The policy explicitly excludes expenses related to hazardous or adventure sports (Excl09).",
        "No, the expenses for the first day of Domiciliary Hospitalisation are not covered; payment will be made from the second day onwards as it requires a 3-day continuity.",
        "The information is not available in the provided documents.",
        "None of the items are payable; they are explicitly listed under non-medical expenses in Annexure I.",
        "No, costs for medicines prescribed by a family member are not eligible for reimbursement.",
        "The claim shall be deemed abandoned, and the company's liability will be extinguished.",
        "The newly-wedded spouse's claim for knee replacement due to a pre-existing condition, contracted less than four months before joining, will not be covered due to the policy's exclusion for pre-existing conditions during the initial waiting period."
    ]
}
```

### Model :- databricks/dbrx-instruct

Model Time :- 14.14s

Model answers -

```json

{
    "answers": [
        "The waiting period for Pre-Existing Diseases (PED) under this policy is waived off, as mentioned in the Other Special Condition Details section.",
        "Based on the provided documents, expenses for cosmetic or plastic surgery are generally excluded, unless the surgery is for reconstruction following an accident, burn(s), or cancer, or as part of medically necessary treatment to remove a direct and immediate health risk to the insured, as certified by the attending medical practitioner.",
        "The policy covers Post-hospitalisation Medical Expenses for a maximum of 60 days.",
        "The room rent limit is not specified in the \"Other Special Conditions\" section of the policy document; instead, it mentions that Room Rent 2% of SI for Normal and 4% of SI for ICU (inclusive of nursing charges) is covered.",
        "A \"Hospital\" is defined in the policy as an institution established for in-patient care and day care treatment of illness and/or injuries, which is registered as a hospital under the Clinical Establishments (Registration and Regulation) Act 2010 or under enactments specified under the Schedule of Section 56(1), and complies with all minimum criteria as specified in the policy.",
        "No, the costs for an organ donor's screening are not covered, as stated in the policy (section 7), and while pre-hospitalization expenses are generally covered under the policy, they must be related to the same illness or injury for which an in-patient hospitalization claim has been accepted, as stated in section 9.",
        "Based on the provided context, treatment received outside of India is listed as an exclusion in section 20, indicating that such treatment is not covered under this policy.",
        "18604250251 is the toll-free number for the TPA, VIDAL HEALTH TPA PRIVATE LTD. This number can be used for general enquiries, cashless approval, claim intimation, and grievances.",
        "No, the policy does not cover expenses related to participation in hazardous or adventure sports, as stated in the policy document exclusion code Excl09.",
        "Based on the provided policy documents, domiciliary hospitalisation is covered when it continues for at least 3 consecutive days, and the expenses for the first day of treatment are included if the conditions are met. However, expenses related to arthritis are not covered under this policy. Therefore, the expenses for the first day of treatment would not be covered for this policyholder's domiciliary hospitalisation for arthritis.",
        "Yes, pre-authorization is required for the dental surgery claim of the 20-year-old dependent child, as it falls under Orthodontic Treatment for Dependent Children below 18 years, for which pre-authorization is explicitly stated as a must in the provided documents.",
        "Error: [429] Too Many Requests\n{'status': 429, 'title': 'Too Many Requests'}",
        "The information is not available in the provided documents regarding the reimbursement of costs for prescribed medicines by a registered Medical Practitioner who is a family member of the insured.",
        "If a policyholder's claim is rejected and they do not file a lawsuit or other proceeding within twelve months from the date of such rejection, the claim shall be deemed to have been abandoned and the insurer's liability shall be extinguished, as stated in section 16 of the policy.",
        "The policy's \"Addition of a Member\" clause allows a newly-wedded spouse to be added to the employer-employee group policy mid-term, and the \"Portability\" clause reduces the waiting period for pre-existing conditions to the extent of prior coverage if the insured person has been continuously covered without any break. However, the \"Waiting Periods\" clause excludes expenses related to the treatment of pre-existing diseases and specific conditions like knee replacement surgery until the expiry of the number of months mentioned in the policy schedule or certificate of insurance. In this scenario, the new member's claim for a knee replacement for a pre-existing condition three months after joining may not be payable due to the waiting period."
    ]
}
```

### Model :- meta/llama-4-maverick-17b-128e-instruct

Model Time :- 9.78s

Model answers -

```json

{
    "answers": [
        "The Pre-Existing Disease Waiting Period is waived under this policy.",
        "Expenses for cosmetic or plastic surgery are not covered unless for reconstruction following an Accident, Burn(s) or Cancer or as part of medically necessary treatment to remove a direct and immediate health risk to the Insured, as certified by the attending Medical Practitioner.",
        "The maximum number of days for which Post-hospitalisation Medical Expenses are covered is 60 days.",
        "The room rent limits are 2% of Sum Insured for normal rooms and 4% of Sum Insured for ICU, inclusive of nursing charges.",
        "A hospital is defined as any institution established for in-patient care and day care treatment of illness and/or injuries, registered with local authorities under the Clinical Establishments (Registration and Regulation) Act 2010 or other specified enactments, and complying with minimum criteria.",
        "No, the costs for an organ donor's screening and pre-hospitalization are not covered, as stated in the exclusions under the Donor Expenses Cover, which specifically mentions that pre-hospitalisation medical expenses and screening expenses of the organ donor are not covered.",
        "Treatment received outside India is not covered under this policy as per exclusion 20, which specifically states that \"Treatment received outside India\" is not eligible for reimbursement.",
        "The toll-free numbers for VIDAL HEALTH TPA are 18604250251 and 080-46267018.",
        "No, expenses related to any treatment necessitated due to participation as a professional in hazardous or adventure sports are excluded under this policy, as stated in exclusion 9, \"Hazardous or Adventure sports (Code- Excl09)\".",
        "The expenses for the first day of treatment are covered because the Domiciliary Hospitalisation continued for at least 3 consecutive days and the condition was due to non-availability of a hospital bed, which is a valid reason as per the policy terms.",
        "Pre-authorization is not required for the 20-year-old dependent child's dental surgery claim due to an accident, as the policy specifically requires pre-authorization for Orthodontic Treatment claims for Dependent Children below 18 years.",
        "The \"cervical collar\" is not payable as per the given context, whereas the context does not explicitly mention \"walker\" in the provided lists, but it is mentioned under non-medical expenses in clause 23 as not payable.",
        "The costs for the prescribed medicines are not reimbursable if the prescription is from a registered Medical Practitioner who is a family member of the insured, except for the proven material costs which are eligible for reimbursement as per the applicable cover.",
        "The claim shall be deemed to have been abandoned and the liability shall be extinguished and shall not be recoverable thereafter.",
        "The policy's clauses on \"Addition of a Member,\" \"Waiting Periods,\" and \"Portability\" will interact to determine that the claim for knee replacement is not payable because the newly-wedded spouse is subject to a waiting period for pre-existing diseases, and since they joined mid-term, they have not completed the required continuous coverage period mentioned in the Policy schedule or Certificate of Insurance."
    ]
}
```

### Model :- mistralai/mistral-7b-instruct-v0.3

Model Time :- 11.36s

Model answers -

```json

{
    "answers": [
        "The waiting period for Pre-Existing Diseases (PED) under this policy is waived.",
        "The information is not available in the provided documents that the expenses for cosmetic or plastic surgery are covered, except for cosmetic or plastic surgery for reconstruction following an Accident, Burn(s), Cancer, or as part of medically necessary treatment to remove a direct and immediate health risk to the Insured.",
        "The Post-hospitalisation Medical Expenses are covered for up to 60 days, according to the provided policy documents.",
        "The room rent limits specified in the \"Other Special Conditions\" are 2% of the Sum Insured for a Normal room and 4% of the Sum Insured for an ICU room, inclusive of nursing charges.",
        "The policy defines a \"Hospital\" as any institution established for in-patient care and day care treatment of illness and/or injuries, which has been registered as a hospital with the local authorities under the Clinical Establishments (Registration and Regulation) Act 2010, or under enactments specified under the Schedule of Section 56(1), and complies with all minimum criteria.",
        "The information is not available in the provided documents regarding whether the costs for an organ donor's screening and pre-hospitalization are covered.",
        "The information is not available in the provided documents regarding if treatment received outside of India is covered under this policy.",
        "The toll-free number for the TPA, VIDAL HEALTH, is 18604250251/080-46267018.",
        "No, the policy explicitly excludes expenses related to participation in hazardous or adventure sports (Code-Excl09).",
        "The information is not available in the provided documents as the policy specifications do not cover arthritis for Domiciliary Hospitalisation, and therefore, no explicit coverage is mentioned for the first day of treatment.",
        "Yes, pre-authorization is required for dental surgery claims of a dependent child below 18 years of age who needs treatment due to an accident.",
        "The cervical collar is not payable according to the documents provided.",
        "The costs for medicines prescribed by a registered Medical Practitioner who is a family member of the insured are reimbursable. [From section F in the context.]",
        "The claim shall be deemed to have been abandoned and liability shall be extinguished, not recoverable thereafter.",
        "The claim for a knee replacement for a pre-existing condition three months after a newly-wedded spouse has been added to an employer-employee group policy mid-term would be subject to the following interactions:\n- The addition of the member would be assessed by the underwriter following the policy's procedures. If accepted, the spouse would be added as an Insured Person.\n- As per the \"Addition of a Member\" clause, a waiting period may still apply for pre-existing conditions, even if they occurred after the addition.\n- According to the \"Waiting Periods\" clause, expenses related to treatment of a pre-existing disease are excluded until the expiry of the number of months, as mentioned in the Policy schedule or Certificate of Insurance, of continuous coverage after the date of inception of the first policy with the Insurer, which in this case would be the date the new member joined the policy. Since the knee replacement surgery is for a pre-existing condition, the claim may not be payable at this time.\n- \"Portability\" clauses state that if the Insured Person is continuously covered without any break, the waiting period for the same would be reduced to the extent of prior coverage. However, in this case, the new member was added mid-term and the specific duration of continuous coverage from the previous policy is not provided, so it's unclear if this clause would apply or reduce the waiting period. Therefore, it's crucial to check the specifics of the new member's prior coverage to determine if the waiting period should be reduced."
    ]
}
```

### Model :- meta/llama-3.2-3b-instruct

Model Time :- 10.71s

Model answers -

```json

{
    "answers": [
        "The waiting period for Pre-Existing Diseases (PED) under this policy is stated as Waived, as indicated in the Insured Details section of the document.",
        "Expenses for cosmetic or plastic surgery are generally not covered unless it is for reconstruction following an accident, burn, or as part of medically necessary treatment to remove a direct and immediate health risk to the Insured and is certified by the attending Medical Practitioner.",
        "The maximum number of days for which Post-hospitalisation Medical Expenses are covered is 60 days.",
        "The policy does not explicitly state the room rent limits specified in the document, but under the \"Room, Boarding and Nursing expenses\" section, it is mentioned that room rental charges will be at 2% of the Sum Insured (SI) for Normal rooms and 4% of SI for ICU rooms, with the insured bearing the difference for any room that is higher than the category/ limit specified.",
        "A Hospital, as defined in Section 56(1) of the Clinical Establishments (Registration and Regulation) Act 2010 or under enactments specified under the Schedule of Section 56(1), is any institution established for in-patient and day care treatment of illness and/or injuries, registered with local authorities, and complying with minimum criteria.",
        "The costs of donor screening are covered by the policy, but the costs of pre-hospitalization expenses are not covered as per the provided documents.",
        "Treatment received outside India is not explicitly stated to be covered under this policy, as the provided documents do not mention coverage for international treatment, but it is mentioned that Treatment means any relevant treatment administered by a Medical Practitioner within the scope of the Policy, indicating local treatment only is covered.",
        "The toll-free number for the TPA VIDAL HEALTH is 18604250251 and 18001203348.",
        "This policy does not cover expenses related to treatment necessitated due to participation in hazardous or adventure sports, including para-jumping, rock climbing, mountaineering, rafting, motor racing, horse racing or scuba diving, hand gliding, sky diving, deep-sea diving, as specified under Code-Excl09.",
        "The insurance policy covers Medical Expenses incurred for the first day of Domiciliary Hospitalisation, as long as the hospitalization continues for at least 3 consecutive days following an illness or injury.",
        "Pre-authorisation is not required for dental treatment due to an accident, but for orthodontic treatment, pre-authorisation must be obtained before treatment starts, and the Insured Person must provide the proposed treatment details, X-rays, and cost estimate prepared by the Dentist before the treatment commences.",
        "The hospital bill includes two charges that fall under the liability of room charges and cannot be compensated by insurance, which are related to the admission of the insured person, specifically Shop No. 21 is \"HVAC\" and Shop No. 7 is \"CAPS\", which would exempt medical equipment used specifically by the policyholder while admitted to the hospital for treatment, neither a \"walker\" nor a \"cervical collar\".",
        "No, the costs for the prescribed medicines reimbursable under the policy are only for medicines, drugs, and other allowable consumables prescribed by the treating Medical Practitioner for the insured person, as explicitly stated in the policy under section E.",
        "If a policyholder's claim is rejected and they do not file a lawsuit within 12 months, the claim shall be deemed to have been abandoned and the issuer of the policy liability shall be extinguished and shall not be recoverable thereafter, as per Section 16 of the provided Policy.",
        "The claim for the knee replacement surgery under this condition will be rejected because, as part of the employer-employee group policy expansion, each additional Insured Person may have an initial waiting period for the treatment of pre-existing conditions, which remains in effect for the specified number of months, in this case, as stated in the policy schedule, or until the initial policy's expiry date, whichever occurs first; therefore, the Insured Person's pre-existing condition for knee replacement falls into this waiting period clause."
    ]
}
```

### Model :- moonshotai/kimi-k2-instruct

Model Time :- 10.50s

Model answers -

```json

{
    "answers": [
        "The waiting period for Pre-Existing Diseases (PED) under this policy is Waived.",
        "Expenses for cosmetic or plastic surgery are not covered as a standard provision under the policy unless for reconstruction following an Accident or as part of medically necessary treatment to remove a direct and immediate health risk to the Insured.",
        "The maximum number of days for which Post-hospitalisation Medical Expenses are covered is 60 as per the Policy Schedule or Certificate of Insurance.",
        "The room rent limits specified in the policy schedule or certificate of insurance are 2% of Studio type (SI) for normal rooms and 4% of SI for ICU rooms, inclusive of nursing charges, and if insured is admitted in a higher category, then the insured will bear the difference of all medical expenses as in the final hospital bill in the same proportion.",
        "A Hospital, as defined in the policy, means any institution established for in-patient care and day care treatment of illness and/or injuries that has been registered as a hospital with the local authorities under the Clinical Establishments (Registration and Regulation) Act 2010 or under enactments specified under the Schedule of Section 56(1) and complies with all minimum criteria.",
        "The costs for an organ donor's screening are not covered under the provided documents.",
        "Treatment received outside India is not covered under this policy, as per the document which explicitly states \"Treatment received outside India.\"",
        "The toll-free number for the TPA, VIDAL HEALTH, is 18604250251/080-46267070/18001203348.",
        "This policy excludes expenses related to any treatment necessitated due to participation as a professional in hazardous or adventure sports, including but not limited to para-jumping, rock climbing, mountaineering, rafting, motor racing, horse racing or scuba diving, hand gliding, sky diving, deep-sea diving.",
        "The insurance policy will pay for the first day of the Domiciliary Hospitalisation as per the medical necessity confirmed by the treating practitioner, given that the hospitalisation continues for at least 3 consecutive days.",
        "The information is that pre-authorisation is required for Orthodontic Treatment claims for Dependent Children below 18 years, in this case, a 20-year-old child.",
        "The information is not available in the provided documents to determine which item, a walker and a cervical collar, is payable, with the context of a policyholder undergoing a covered surgery, as it specifically states non-medical expenses for the diagnosis and treatment and that these should be referred to the Annexure I “Non-Medical Expenses” section.",
        "According to the policy, expenses for medicines, drugs, and other allowable consumables prescribed by the treating Medical Practitioner, including those prescribed by a family member, are eligible for reimbursement.",
        "If a policyholder's claim is rejected and they do not file a lawsuit within 12 months, the claim shall be deemed to have been abandoned and the Company's liability shall be extinguished and not be recoverable thereafter.",
        "The claim for the knee replacement surgery of the newly-wedded spouse will not be payable as the pre-existing condition exclusion in relation to pre-existing diseases mentioned in clause ii of the Specific Waiting Period (Code-Excl02) will apply, reducing the waiting period to the extent of prior coverage, considering continuous coverage without any break as defined under the applicable norms on portability stipulated by IRDAI."
    ]
}
```

### Model :- marin/marin-8b-instruct

Model Time :- 10.82s

Model answers -

```json

{
    "answers": [
        "The waiting period for Pre-Existing Diseases (PED) is mentioned in the context as: \"As Per minimum limits of UGHIP.\"",
        "The information is not available in the provided documents.",
        "Error: [###] The model `marin/marin-8b-instruct` does not exist.\n{'error': 'The model `marin/marin-8b-instruct` does not exist.'}",
        "Room rent limits are 2% of Sum Insured for normal rooms and 4% of Sum Insured for ICU rooms.",
        "Error: [###] The model `marin/marin-8b-instruct` does not exist.\n{'error': 'The model `marin/marin-8b-instruct` does not exist.'}",
        "The information is not available in the provided documents.",
        "Treatment received outside India is not covered under this policy, as specified in section 20 of the given document, which categorically states that the treatment \"received outside India\" will not be reimbursed.",
        "Error: [###] The model `marin/marin-8b-instruct` does not exist.\n{'error': 'The model `marin/marin-8b-instruct` does not exist.'}",
        "Error: [###] The model `marin/marin-8b-instruct` does not exist.\n{'error': 'The model `marin/marin-8b-instruct` does not exist.'}",
        "Error: [###] The model `marin/marin-8b-instruct` does not exist.\n{'error': 'The model `marin/marin-8b-instruct` does not exist.'}",
        "Error: [###] The model `marin/marin-8b-instruct` does not exist.\n{'error': 'The model `marin/marin-8b-instruct` does not exist.'}",
        "Error: [###] The model `marin/marin-8b-instruct` does not exist.\n{'error': 'The model `marin/marin-8b-instruct` does not exist.'}",
        "No, the costs for the prescribed medicines are not reimbursable if the prescription is from a person who stays with the insured person, and they are not registered as Medical Practitioners under the respective Medical Councils. This falls under the eligibility criteria specified in the insurance policy for reimbursement. In case of admission to a room at rates exceeding the limits mentioned in the Policy Schedule/Certificate of Insurance, the reimbursement/payment of all associated medical expenses incurred at the Hospital shall be effected in the same proportion as the admissible rate per day bears to the actual rate per day of Room Rent.",
        "Error: [###] The model `marin/marin-8b-instruct` does not exist.\n{'error': 'The model `marin/marin-8b-instruct` does not exist.'}",
        "A newly-wedded spouse added to the policy as an insured person three months after marriage will still be covered for her knee replacement surgery with pre-existing condition, as the specified waiting period for pre-existing disease does not start re-accelerating from the date of her joining but rather from first policy inception. The two months during her coverage prior to needing the surgery accumulate towards the waiting period. The policy does not require the condition to be declared at the time of the addition as a Member unless specifically required by the insurer and accepted. If another policy is in place or she had prior continuous coverage for the same condition, IRDAI's portability norms may reduce the waiting period proportionately. Therefore, if the waiting period is incomplete at the time of the operation, the claim for pre-existing condition-operated surgery will not be payable."
    ]
}
```

### Model :- mistralai/mistral-small-3.1-24b-instruct-2503

Model Time :- 16.55s

Model answers -

```json

{
    "answers": [
        "The waiting period for Pre-Existing Diseases under this policy is currently waived off.",
        "Expenses for cosmetic or plastic surgery are generally not covered, except for reconstructive surgery following an accident, burns, cancer, or medically necessary treatment to remove a direct and immediate health risk, which must be certified by the attending medical practitioner.",
        "The maximum number of days for which Post-hospitalisation Medical Expenses are covered is 60 days.",
        "The room rent limits specified in the \"Other Special Conditions\" are 2% of the sum insured for a normal room and 4% of the sum insured for ICU.",
        "A hospital is defined as any institution established for in-patient care and day care treatment of illness and/or injuries. It must be registered with local authorities under the Clinical Establishments Act of 2010 or under similar enactments, or it must comply with all minimum criteria specified.",
        "The costs for organ donor's screening and pre-hospitalization medical expenses are not covered by the policy.",
        "Treatment received outside India is not covered under this policy.",
        "The toll-free numbers for VIDAL HEALTH TPA are 18604250251 and 08046267018.",
        "The policy explicitly excludes expenses related to treatment necessitated due to participation as a professional in hazardous or adventure sports, including various activities like para-jumping, rock climbing, and scuba diving.",
        "The information is not available in the provided documents.",
        "Pre-authorization is not required for a 20-year-old dependent child needing dental surgery due to an accident if hospitalization is required, as it is covered under GIPSA PN Clause.",
        "For a policyholder undergoing a covered surgery, the cervical collar is payable only if it is required post-surgery but the walker is not payable.",
        "The costs for prescribed medicines are only reimbursable if the medical practitioner is registered under the respective Medical Councils and not just a family member, as care by family members or unregistered practitioners is not covered.",
        "The claim will be deemed abandoned, and the company will not have further liability for it.",
        "The policy's \"Waiting Periods\" clause will exclude expenses related to the treatment of pre-existing conditions like knee replacement for a specified number of months, the length of which needs to be checked by referring to the policy schedule. So, if no continuous coverage without a break exists before the policy or to the issue of portability, and the waiting period in the policy has not been met, the claim will not be covered."
    ]
}
```

### Model :- qwen/qwen2.5-7b-instruct

Model Time :- 17.93s

Model answers -

```json

{
    "answers": [
        "Pre-Existing Disease Waiting Period is waived under this policy.",
        "Expenses for cosmetic or plastic surgery or any treatment to change appearance are not covered unless for reconstruction following an accident, burns, cancer, or as part of medically necessary treatment to remove a direct and immediate health risk, which must be certified by the attending medical practitioner.",
        "The maximum number of days for which Post-hospitalisation Medical Expenses are covered is 60 days.",
        "The room rent limits specified in the \"Other Special Conditions\" are 2% of the sum insured for normal rooms and 4% of the sum insured for ICU rooms (inclusive of nursing charges).",
        "According to the policy, a Hospital means any institution established for in-patient care and day care treatment of illness and/or injuries and which has been registered as a hospital with the local authorities under the Clinical Establishments (Registration and Regulation) Act 2010 or under enactments specified under the Schedule of Section 56(1) and the said act or complies with all minimum criteria as under: 6/24/25, 5:21 PM slportal.uiic.in/Configurator/HTMLReportSource/rei3ckas5sidov552op4vm45UniGroupHealthInsurancePolicy_202506192166603PS.htm 19/37",
        "The costs for an organ donor's screening and pre-hospitalization medical expenses are not covered, as explicitly stated in the context.",
        "Treatment received outside India is not covered under this policy according to context 19.",
        "The toll-free number for VIDAL HEALTH TPA is 18604250251/08046267018.",
        "Expenses related to participation in hazardous or adventure sports are excluded under this policy.",
        "The expenses for the first day of treatment are covered provided the policy terms for Domiciliary Hospitalisation are met, specifically that the treatment continues for at least 3 consecutive days and a Medical Practitioner confirms it was medically required due to the unavailable hospital bed.",
        "Pre-authorization is not required for a 20-year-old dependent child's claim for dental surgery due to an accident as the policy covers dental expenses for dependent children below 18 years, and pre-authorization is specified only for those below 18 years.",
        "The cervical collar is not payable, but the walker may be payable if it is used during hospitalization and meets the terms of the policy; otherwise, it is considered a non-medical expense.",
        "The costs for the prescribed medicines are reimbursable only if they are supported by a certification/diagnosis/Treatment by a registered Medical Practitioner under the respective Medical Councils and not by a family member, unless the proven material costs are eligible for reimbursement as per the applicable cover.",
        "The claim shall be deemed to have been abandoned and the Company's liability shall be extinguished and shall not be recoverable thereafter.",
        "The policy's clauses on \"Addition of a Member,\" \"Waiting Periods,\" and \"Portability\" will likely result in the new member being subject to a waiting period for the pre-existing condition since the knee replacement falls under a listed specific disease, and the waiting period for such conditions still applies even if contracted after the policy or declared and accepted without a specific exclusion. However, if the member was continuously covered without any break as defined under the applicable norms on portability stipulated by IRDAI, the waiting period for the same could be reduced to the extent of prior coverage, but the initial waiting period would still apply before the claim becomes payable."
    ]
}
```

### Model :- tiiuae/falcon3-7b-instruct

Model Time :- 11.24

Model answers -

```json

{
    "answers": [
        "The information is not available in the provided documents.",
        "Expenses for cosmetic or plastic surgery are generally not covered unless the procedure is for reconstruction following an Accident, Burn(s), Cancer, or as part of medically necessary treatment to remove a direct and immediate health risk.",
        "The maximum number of days for which Post-hospitalisation Medical Expenses are covered is 60 days.",
        "The room rent limits specified in the \"Other Special Conditions\" are 2% of SI (Salary in Considerations) for Normal Rooms and 4% of SI for ICU (Intensive Care Unit) rooms.",
        "According to the policy, a \"Hospital\" refers to an institution established for in-patient care and day care treatment of illness and/or injuries, registered with local authorities under the Clinical Establishments (Registration and Regulation) Act 2010 or specified enactments, and conforming to minimum criteria.",
        "The costs for an organ donor's screening and pre-hospitalization are not covered under the Policy.",
        "Treatment received outside India is covered under this policy, up to specific limits.",
        "The information is not available in the provided documents.",
        "The policy does not cover expenses related to participation in hazardous or adventure sports as these are explicitly excluded (Code- Excl09).",
        "Yes, the expenses for the first day of Domiciliary Hospitalisation are covered, provided that all other conditions are met, including the specific requirements stated in the policy for the treatment of arthritis.",
        "For a 20-year-old dependent child requiring dental surgery due to an accident, pre-authorization is mandatory as per the provided policy terms.",
        "The information is not available in the provided documents.",
        "The information is not available in the provided documents.",
        "The claim is deemed abandoned, and the insurer's liability is extinguished.",
        "For a newly-wedded spouse added mid-term, and needing a knee replacement surgery for a pre-existing condition three months later, the Policy's clauses on addition of a member, waiting periods, and portability might lead to the exclusion of the claim due to the pre-existing disease waiting period, unless the longer of the two waiting periods applies or if coverage was continuous without a break. The exact payout depends on the Policy schedule specifics regarding the waiting period for pre-existing diseases."
    ]
}
```

---
