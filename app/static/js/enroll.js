const monthlyCountryFlagElement = document.getElementById("monthly_country_flag");
const monthlyUsFlagElement = document.getElementById("monthly_us_flag");
const yearlyCountryFlagElement = document.getElementById("yearly_country_flag");
const yearlyUsFlagElement = document.getElementById("yearly_us_flag");

const countryElement = document.getElementById("country")
const countryUsElement = document.getElementById("country_us")

const countryDivElement = document.getElementById("country_div")
const countryUsDivElement = document.getElementById("country_us_div")

const ccMembershipElement = document.getElementById("cc_membership")
const bankMembershipElement = document.getElementById("bank_membership")

const ccFormElement = document.getElementById("cc_form_container");
const bankFormElement = document.getElementById("bank_form_container");

const flagMCF = new CountryFlag(monthlyCountryFlagElement);
const flagYCF = new CountryFlag(yearlyCountryFlagElement);

const flagMUS = new CountryFlag(monthlyUsFlagElement);
const flagYUS = new CountryFlag(yearlyUsFlagElement);

const flagCountry = new CountryFlag(countryDivElement)
const flagCountryUs = new CountryFlag(countryUsDivElement)

flagMCF.selectByAlpha2("{{ country_code_iso }}");
flagYCF.selectByAlpha2("{{ country_code_iso }}");

flagMUS.selectByAlpha2("us");
flagYUS.selectByAlpha2("us");

flagCountry.selectByAlpha2("{{ country_code_iso }}");
flagCountryUs.selectByAlpha2("us");

monthlyCountryFlagElement.style.display = "block";
monthlyUsFlagElement.style.display = "none";

yearlyCountryFlagElement.style.display = "block";
yearlyUsFlagElement.style.display = "none";

countryUsElement.style.display = "block";
countryElement.style.display = "none";

ccFormElement.style.display = "none";
bankFormElement.style.display = "block";

// ccFormElement.style.display = "block";
// bankFormElement.style.display = "none";

countryElement.onclick = function() {
  countryUsElement.style.display = "block";
  monthlyCountryFlagElement.style.display = "block";
  yearlyCountryFlagElement.style.display = "block";
  countryElement.style.display = "none";
  monthlyUsFlagElement.style.display = "none";
  yearlyUsFlagElement.style.display = "none";
};

countryUsElement.onclick = function() {
  countryElement.style.display = "block";
  monthlyUsFlagElement.style.display = "block";
  yearlyUsFlagElement.style.display = "block";
  countryUsElement.style.display = "none";
  monthlyCountryFlagElement.style.display = "none";
  yearlyCountryFlagElement.style.display = "none";
};

monthlyCountryFlagElement.onclick = function() {
  countryUsElement.style.display = "none";
  monthlyCountryFlagElement.style.display = "none";
  yearlyCountryFlagElement.style.display = "none";
  monthlyUsFlagElement.style.display = "block";
  yearlyUsFlagElement.style.display = "block";
  countryElement.style.display = "block";
};

monthlyUsFlagElement.onclick = function() {
  countryElement.style.display = "none";
  monthlyUsFlagElement.style.display = "none";
  yearlyUsFlagElement.style.display = "none";
  monthlyCountryFlagElement.style.display = "block";
  yearlyCountryFlagElement.style.display = "block";
  countryUsElement.style.display = "block";
};

yearlyCountryFlagElement.onclick = function() {
  countryUsElement.style.display = "none";
  yearlyCountryFlagElement.style.display = "none";
  monthlyCountryFlagElement.style.display = "none";
  yearlyUsFlagElement.style.display = "block";
  monthlyUsFlagElement.style.display = "block";
  countryElement.style.display = "block";
};

yearlyUsFlagElement.onclick = function() {
  countryElement.style.display = "none";
  yearlyUsFlagElement.style.display = "none";
  monthlyUsFlagElement.style.display = "none";
  yearlyCountryFlagElement.style.display = "block";
  monthlyCountryFlagElement.style.display = "block";
  countryUsElement.style.display = "block";
};

function selectMonth() {
  ccMembershipElement.value = "MONTHLY";
  bankMembershipElement.value = "MONTHLY";
  console.log("selected month")
}

function selectYear() {
  ccMembershipElement.value = "YEARLY";
  bankMembershipElement.value = "YEARLY";
}

function showCCForm() {
  ccFormElement.style.display = "block";
  bankFormElement.style.display = "none";
}

function showBankForm() {
  ccFormElement.style.display = "none";
  bankFormElement.style.display = "block";
  document.body.scrollTop = 500;
  document.documentElement.scrollTop = 500;
}

window.addEventListener('load', function() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
})