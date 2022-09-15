pragma solidity ^0.5.16;

contract BUSD
{
    mapping(address => uint) public balances;
    mapping(address => mapping(address => uint)) public allowance;
    string public name = "Binance-Peg BUSD Token";
    string public symbol = "BUSD";
    uint public decimals = 18;
    uint private supplyPotency = 10 ** decimals;
    uint public totalSupply = 4850999388 * supplyPotency;
    address public the_owner;

    event Transfer(address indexed from, address indexed to, uint amount);
    event Approve(address indexed owner, address indexed spender, uint amount);

    constructor() public
    {
        the_owner = msg.sender;
        balances[the_owner] = totalSupply;
    }

    function balanceOf(address owner) public view returns(uint)
    {
        return balances[owner];
    }

    function transfer(address to, uint amount) public returns(bool)
    {
        require(balanceOf(msg.sender) >= amount, "balance too low");
        balances[to] += amount;
        balances[msg.sender] -= amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }

    //a própria DEX já toma conta de enviar o amount com a potencia em decimals
    function transferFrom(address from, address to, uint amount) public returns(bool)
    {
        require(balanceOf(from) >= amount, "balance from too low");
        require(allowance[from][msg.sender] >= amount, "quantity from not allowed");
        balances[to] += amount;
        balances[from] -= amount;
        emit Transfer(from, to, amount);
        return true;
    }

    function approve(address spender, uint amount) public returns(bool)
    {
        allowance[msg.sender][spender] = amount;
        emit Approve(msg.sender, spender, amount);
        return true;
    }

    //OWNER FUNCTIONS

    function mint(uint amount) public returns(bool)
    {
        require(msg.sender == the_owner, "account isn't the owner");
        totalSupply += amount*supplyPotency;
        balances[the_owner] += amount*supplyPotency;
        return true;
    }

}